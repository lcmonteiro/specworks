# Project and workspace

## `specworks version`

Print the specworks version.

```console
$ specworks version
0.1.0
```

## `specworks init`

Create `<dir>.yml` and `<dir>/changes/`, link to a parent project, and install
the agent skills.

```text
specworks init [PATH] [--dir NAME] [--name NAME] [--diagram-theme THEME]
               [--no-link] [--tools auto|all|claude,copilot] [--no-skills]
```

| Option | Default | Meaning |
|---|---|---|
| `PATH` | `.` | project (or module) root |
| `--dir` | `specworks` | workflow folder name, also the config name: `--dir spec` → `spec.yml` + `spec/` |
| `--name` | folder name | module name when linking to a parent project |
| `--diagram-theme` | `neutral-default` | diagram theme for the workspace, by name or number (`specworks diagrams --themes`) |
| `--no-link` | | do not register as a module of a parent specworks project |
| `--tools` | `auto` | AI tools to install skills for: `auto` (detected; all if none), `all`, or a list of `claude`, `copilot` |
| `--no-skills` | | do not install agent skills |

Run under an existing project, `init` creates a module and links it to its
parent (unless `--no-link`).

```console
$ specworks init --dir spec --tools claude
created spec.yml
ready   spec/changes/
tools   Claude Code
skill   .claude/skills/specworks-adopt/SKILL.md
skill   .claude/skills/specworks-build/SKILL.md
skill   .claude/skills/specworks-close/SKILL.md
skill   .claude/skills/specworks-code/SKILL.md
skill   .claude/skills/specworks-design/SKILL.md
skill   .claude/skills/specworks-refine/SKILL.md
skill   .claude/skills/specworks-review/SKILL.md
skill   .claude/skills/specworks-specify/SKILL.md
skill   .claude/skills/specworks-test/SKILL.md
skill   .claude/skills/specworks-validate/SKILL.md
```

**Used by**: [/specworks-adopt](Skills-Adopt) (stage 1), with your go-ahead. Other skills
never run it on their own: on `"root": null` they stop and ask.

## `specworks skills`

Install or refresh the agent skills, e.g. after upgrading specworks. Shared
text (`<!-- specworks:include ... -->`) is filled in at install time.

```text
specworks skills [--tools auto|all|claude,copilot]
```

```console
$ specworks skills --tools claude
tools   Claude Code
skill   .claude/skills/specworks-adopt/SKILL.md
...
skill   .claude/skills/specworks-validate/SKILL.md
```

## `specworks context`

The inherited context, every capability of the workspace, the modules and the
changes in flight. The first command of every skill.

```text
specworks context [--json] [--all]
```

| Option | Meaning |
|---|---|
| `--all` | changes of every module, not only the current one |

**Text**

```console
$ specworks context --all
root:    /work/shortlink
module:  (top)
modules:
  (top)                    .  *
capabilities:
  links                    src/shortlink
  qr                       src/shortlink/qr
changes:
  add-qr-codes             design
```

**JSON**

```json
{
  "root": "/work/shortlink",
  "module": "(top)",
  "dir": "spec",
  "changesDir": "spec/changes",
  "context": "Python 3.12 library, standard library only. Public API lives in src/shortlink/.\nErrors are raised as subclasses of shortlink.errors.ShortlinkError.",
  "contextChain": [
    { "module": "(top)", "context": "Python 3.12 library, standard library only. ..." }
  ],
  "commands": {
    "test": "python -m pytest -q -p no:cacheprovider -o pythonpath=src tests",
    "lint": "ruff check src tests"
  },
  "modules": [
    { "name": "(top)", "path": ".", "dir": "spec", "changesDir": "spec/changes", "current": true }
  ],
  "missingModules": [],
  "capabilities": [
    {
      "name": "links",
      "module": "(top)",
      "path": "src/shortlink",
      "description": "Create short codes for URLs and resolve them",
      "docsPath": "src/shortlink/docs",
      "hasSpec": false,
      "prefix": "LINK",
      "deltaPath": "specs/links/spec.md"
    }
  ],
  "changes": []
}
```

| Field | Meaning |
|---|---|
| `root` | the workspace root; `null` when no config is found (not set up) |
| `module`, `dir`, `changesDir` | the current module and its folders |
| `context`, `contextChain` | constraints merged top level → current module, and each one's own |
| `commands` | the project commands (`test`, `lint`, ...), a module's overriding the top level's |
| `modules`, `missingModules` | every module; modules listed by a parent but not checked out |
| `capabilities` | every capability of the workspace: code `path`, `docsPath`, `hasSpec`, `prefix`, `deltaPath` |
| `changes` | active changes (all modules with `--all`) |

**Used by**: every skill, first step ([0. Set up the project](Tutorial-Setup)).

## `specworks module add` / `module list`

Link a folder as a module of the current project (creating its config if
needed), and list the modules.

```text
specworks module add PATH [--name NAME] [--json]
specworks module list [--json]
```

```console
$ specworks module add services/analytics
linked  services/analytics as module 'analytics'
$ specworks module list
(top)                    .  *
analytics                services/analytics
```

The parent's config gets:

```yaml
modules:
  analytics: services/analytics
```

From inside the module, `context` shows it as current and inherits the
parent's context and commands; its changes are named `analytics:<name>`:

```console
$ specworks new track-clicks --module analytics --json
{
  "name": "track-clicks",
  "ref": "analytics:track-clicks",
  "module": "analytics",
  "path": "services/analytics/spec/changes/track-clicks",
  "phase": "refine",
  "created": "2026-10-17T21:01:04",
  "skipSpecs": false
}
$ specworks list --all
add-qr-codes                     design
analytics:track-clicks           refine
```
