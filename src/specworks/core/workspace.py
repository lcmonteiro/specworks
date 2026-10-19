"""Workspace: a top-level project and the modules (sub-projects) linked to it.

Like git submodules, the parent lists each module explicitly in its config
(``modules: {name: path}``) and every module is a complete project with its
own config. Commands act on the *current* module, the one
nearest to the working directory, but see the whole tree:

- the workflow folder name is set by the top level's config file name
  (``spec.yml`` -> ``spec/``) and shared by every module: each module has a
  ``spec.yml`` and a ``spec/`` folder too;
- context is inherited: top-level context first, then each module down to the
  current one;
- capabilities and changes of other modules are addressed as ``module:name``,
  where nested modules are joined with ``/`` (``billing/tax:rates``).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import CONFIG_EXT, Capability, Config, ConfigError, config_name, find_config, find_root, is_config_file, load_config
from .errors import SpecworksError

SEP = ":"


# @req REQ-PROJ-004
def capability_prefix(module_name: str, name: str, prefix: str = "") -> str:
    """The ID prefix (REQ-<prefix>-NNN) of a capability: its own ``prefix:``, else its module path and name in upper case.

    ``billing/tax`` + ``rates`` -> ``BILLING-TAX-RATES``.
    """
    return prefix or "-".join([*module_name.split("/"), name] if module_name else [name]).upper()


@dataclass
class Module:
    name: str  # "" for the top level, "billing" or "billing/tax" below it
    config: Config
    parent: Module | None = None
    children: list[Module] = field(default_factory=list)

    @property
    def root(self) -> Path:
        return self.config.root

    @property
    def label(self) -> str:
        return self.name or "(top)"

    def qualify(self, item: str) -> str:
        return f"{self.name}{SEP}{item}" if self.name else item

    def lineage(self) -> list[Module]:
        """Modules from the top level down to this one."""
        chain: list[Module] = []
        node: Module | None = self
        while node is not None:
            chain.append(node)
            node = node.parent
        return chain[::-1]

    def walk(self) -> Iterator[Module]:
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass
class MissingModule:
    """A module listed by its parent whose folder has no config (e.g. a submodule not checked out)."""

    name: str
    path: Path


@dataclass
class Workspace:
    top: Module
    current: Module
    missing: list[MissingModule] = field(default_factory=list)

    @property
    def root(self) -> Path:
        return self.top.root

    def rel(self, path: Path) -> str:
        """Path relative to the workspace root, the base for every path the CLI prints."""
        return path.resolve().relative_to(self.root).as_posix() or "."

    def modules(self) -> list[Module]:
        return list(self.top.walk())

    def module(self, name: str) -> Module:
        for mod in self.modules():
            if mod.name == name:
                return mod
        known = ", ".join(m.name for m in self.modules() if m.name) or "none"
        raise ConfigError(f"unknown module '{name}' (known modules: {known})")

    def split(self, ref: str) -> tuple[Module | None, str]:
        """``billing:add-x`` -> (billing module, "add-x"); ``add-x`` -> (None, "add-x")."""
        if SEP in ref:
            module_name, _, item = ref.rpartition(SEP)
            return self.module(module_name), item
        return None, ref

    # @req REQ-PROJ-007
    def context_chain(self, module: Module | None = None) -> list[dict]:
        """Inherited context, top level first. A module adds to its parents' context; it cannot drop it."""
        return [
            {"module": m.label, "context": m.config.context.strip()}
            for m in (module or self.current).lineage()
            if m.config.context.strip()
        ]

    def merged_context(self, module: Module | None = None) -> str:
        chain = self.context_chain(module)
        if len(chain) == 1:
            return chain[0]["context"]
        return "\n\n".join(f"[{item['module']}]\n{item['context']}" for item in chain)

    # @req REQ-PROJ-007
    def commands(self, module: Module | None = None) -> dict[str, str]:
        """Commands for a module: the top level's, overridden key by key down to the module."""
        merged: dict[str, str] = {}
        for node in (module or self.current).lineage():
            merged.update(node.config.commands)
        return merged

    def owner(self, path: Path) -> Module:
        """The innermost module whose folder holds ``path`` (a path inside the workspace)."""
        return max((m for m in self.modules() if path.is_relative_to(m.root)), key=lambda m: len(m.root.parts))

    def capabilities(self) -> list[tuple[Module, Capability]]:
        return [(m, cap) for m in self.modules() for cap in m.config.capabilities.values()]

    def prefixes(self) -> dict[str, str]:
        """ID prefix -> the registered capability (``module:name``) that uses it."""
        return {capability_prefix(m.name, cap.name, cap.prefix): m.qualify(cap.name) for m, cap in self.capabilities()}

    def docs_folder(self, module: Module, path: str) -> Path:
        """The living-docs folder a capability on ``path`` (relative to ``module``) writes to, resolved."""
        return (module.root / path.strip().rstrip("/") / module.config.docs_dir).resolve()

    def docs_folders(self) -> dict[Path, str]:
        """Resolved living-docs folder -> the registered capability (``module:name``) that uses it."""
        return {self.docs_folder(m, cap.path): m.qualify(cap.name) for m, cap in self.capabilities()}


def _links_to(parent: Config, child_root: Path) -> str | None:
    """Name under which ``parent`` lists ``child_root`` as a module, if it does."""
    for name, path in parent.modules.items():
        if (parent.root / path).resolve() == child_root:
            return name
    return None


def _may_link(directory: Path, child_root: Path) -> bool:
    """Whether the (invalid) configs in ``directory`` may list ``child_root`` as a module; True when unreadable."""
    for path in directory.glob(f"*{CONFIG_EXT}"):
        if not is_config_file(path):
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            return True
        modules = raw.get("modules") if isinstance(raw, dict) else None
        if isinstance(modules, dict) and any(isinstance(p, str) and (directory / p).resolve() == child_root for p in modules.values()):
            return True
    return False


# @req REQ-PROJ-006
def load_module_config(root: Path, name: str, workspace_dir: str) -> Config | None:
    """Config of a module, which must use the workspace's file name (<dir>.yml); None if it has none."""
    found = find_config(root)
    if found is None:
        return None
    if found.name != config_name(workspace_dir):
        raise ConfigError(
            f"module '{name}' uses {found.name} ({found.stem}/), but the workspace uses "
            f"{config_name(workspace_dir)} ({workspace_dir}/); rename {found} to {config_name(workspace_dir)} "
            f"and its {found.stem}/ folder to {workspace_dir}/"
        )
    return load_config(root, workspace_dir)


# @req REQ-PROJ-006
def _load_tree(config: Config, name: str, parent: Module | None, missing: list[MissingModule]) -> Module:
    module = Module(name=name, config=config, parent=parent)
    for child_name, child_path in config.modules.items():
        child_root = (config.root / child_path).resolve()
        full_name = f"{name}/{child_name}" if name else child_name
        child_config = load_module_config(child_root, full_name, config.dir)
        if child_config is None:
            missing.append(MissingModule(name=full_name, path=child_root))
            continue
        module.children.append(_load_tree(child_config, full_name, module, missing))
    return module


def require_workspace(start: Path) -> Workspace:
    """The workspace containing ``start``, which must exist (e.g. right after writing its config)."""
    ws = load_workspace(start)
    if ws is None:
        raise ConfigError(f"no specworks config in {start} or its parents")
    return ws


# @req REQ-PROJ-006
def load_workspace(start: Path | None = None) -> Workspace | None:
    """Load the workspace containing ``start``; None when there is no specworks config above it.

    The nearest config is the current module. Walking up, each ancestor that
    lists the current top as a module becomes the new top; the first ancestor
    that does not link to it ends the search (an unrelated outer project).
    """
    nearest = find_root(start)
    if nearest is None:
        return None
    top_root = nearest
    for ancestor in nearest.parents:
        try:
            if find_config(ancestor) is None:
                continue
            parent = load_config(ancestor)
        except SpecworksError:  # an invalid or unreadable config
            # A broken config only matters here when it may be the parent of this project.
            if not _may_link(ancestor, top_root):
                break
            raise
        if _links_to(parent, top_root) is None:
            break
        top_root = ancestor

    missing: list[MissingModule] = []
    top = _load_tree(load_config(top_root), "", None, missing)
    current = next(m for m in top.walk() if m.root == nearest)
    ws = Workspace(top=top, current=current, missing=missing)
    _check_prefixes(ws)
    _check_docs_folders(ws)
    return ws


# @req REQ-PROJ-005
def _check_prefixes(ws: Workspace) -> None:
    """Every capability has its own ID prefix, or two of them would hand out the same requirement IDs."""
    owners: dict[str, str] = {}
    for module, cap in ws.capabilities():
        prefix, ref = capability_prefix(module.name, cap.name, cap.prefix), module.qualify(cap.name)
        if prefix in owners:
            raise ConfigError(
                f"capabilities {owners[prefix]} and {ref} both use the ID prefix {prefix}; "
                f"give one of them its own 'prefix:' in its config (IDs already written keep the prefix they have)"
            )
        owners[prefix] = ref


# @req REQ-PROJ-016
def _check_docs_folders(ws: Workspace) -> None:
    """Every capability has its own living-docs folder, or close would write two capabilities' specs into one file."""
    owners: dict[Path, str] = {}
    for module, cap in ws.capabilities():
        folder, ref = ws.docs_folder(module, cap.path), module.qualify(cap.name)
        if folder in owners:
            where = ws.rel(folder) if folder.is_relative_to(ws.root) else folder.as_posix()
            raise ConfigError(
                f"capabilities {owners[folder]} and {ref} both use the docs folder {where}; give one of them its own 'path:'"
            )
        owners[folder] = ref
