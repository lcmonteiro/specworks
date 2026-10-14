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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .config import Capability, Config, ConfigError, config_name, find_config, find_root, load_config

SEP = ":"


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

    def commands(self, module: Module | None = None) -> dict[str, str]:
        """Commands for a module: the top level's, overridden key by key down to the module."""
        merged: dict[str, str] = {}
        for node in (module or self.current).lineage():
            merged.update(node.config.commands)
        return merged

    def capabilities(self) -> list[tuple[Module, Capability]]:
        return [(m, cap) for m in self.modules() for cap in m.config.capabilities.values()]


def _links_to(parent: Config, child_root: Path) -> str | None:
    """Name under which ``parent`` lists ``child_root`` as a module, if it does."""
    for name, path in parent.modules.items():
        if (parent.root / path).resolve() == child_root:
            return name
    return None


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
        if find_config(ancestor) is None:
            continue
        if _links_to(load_config(ancestor), top_root) is None:
            break
        top_root = ancestor

    missing: list[MissingModule] = []
    top = _load_tree(load_config(top_root), "", None, missing)
    current = next(m for m in top.walk() if m.root == nearest)
    return Workspace(top=top, current=current, missing=missing)
