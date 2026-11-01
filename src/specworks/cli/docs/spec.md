# cli

## Purpose

The `specworks` command line: the conventions every command follows (JSON
output, errors, paths), how a change is named on the command line, and what each
command adds on top of the capabilities it calls.

## Requirements

### Requirement: REQ-CLI-001 Output and errors

Every command an agent reads SHALL support `--json`. An expected failure SHALL
print `{"error": …}` with `--json`, or `error: …` on stderr without it, and exit
1, including a failure raised before a command runs (a broken config or change
file). With no project, the answer SHALL be `{"root": null}` with a fix, and
exit 1. Paths in the output SHALL be relative to the workspace root.

#### Scenario: AC-CLI-001.1 No project

- **WHEN** a command runs where no specworks config is found
- **THEN** it exits 1 and its JSON has `"root": null`

#### Scenario: AC-CLI-001.2 An error

- **WHEN** a change file is broken, whether a command names the change or `list`/`context` read every change
- **THEN** the command exits 1 with `{"error": …}` (`--json`) or `error: …` on stderr

#### Scenario: AC-CLI-001.3 Relative paths

- **WHEN** `init` runs, at the top level or in a module
- **THEN** it prints paths relative to the workspace root, never the absolute root

### Requirement: REQ-CLI-002 Naming a change

A change SHALL be named as `module:name` (exact) or by its bare name: the
current module's first, else the only module that has one. A bare name in
several other modules SHALL be refused, listing the qualified names. An archived
change SHALL be refused by every command but `status`, which reads it by name or
by archive folder. A path into the archive is not a change name.

#### Scenario: AC-CLI-002.1 A bare name in another module

- **WHEN** a bare name exists only in another module
- **THEN** it resolves to that module's change (`billing/tax:add-vat`)

#### Scenario: AC-CLI-002.2 The same name in several modules

- **WHEN** a bare name exists in several modules but not the current one
- **THEN** the command fails listing `billing:cleanup` and `billing/tax:cleanup`; a qualified name works

#### Scenario: AC-CLI-002.3 The current module first

- **WHEN** a bare name exists in the current module and another one
- **THEN** the current module's change is used

#### Scenario: AC-CLI-002.4 An archived change

- **WHEN** a command other than `status` names an archived change, or a name no module has
- **THEN** it fails saying where the change is archived, or that it is not found, active or archived

#### Scenario: AC-CLI-002.5 Status of an archived change

- **WHEN** `status` names an archived change by name or by archive folder
- **THEN** it shows the change as archived, with its path (and its reason if abandoned)

#### Scenario: AC-CLI-002.6 An archive path

- **WHEN** a command names `archive/<date>-<name>`
- **THEN** it is refused as not kebab-case, and the archived change is untouched

### Requirement: REQ-CLI-003 init

`specworks init` SHALL create `.specworks/config.yml`,
`.specworks/changes/active/` and `.specworks/changes/archive/`, and
install the agent skills unless `--no-skills` is given. Inside a specworks
project, it SHALL link the new project as a module (named by its full path)
unless `--no-link` is given, and SHALL refuse a folder that holds a module of
the workspace (naming it) before writing anything. It SHALL refuse a folder
that is not inside a git repository, saying to run `git init`, before writing
anything. `--diagram-theme` SHALL apply only to a new top-level config;
elsewhere it SHALL print a note saying it wasn't applied. When it installs
skills at a top level whose config saves no tools and no `--tools` is given,
it SHALL ask which tools the project uses if it runs in a terminal, offering
the detected tools as the default, and SHALL use the detected tools (`auto`)
without asking otherwise; the tools it installs SHALL be saved in the config.

#### Scenario: AC-CLI-003.1 A new project

- **GIVEN** the folder is empty and inside a git repository
- **WHEN** `init` runs there
- **THEN** it creates `.specworks/config.yml`, `.specworks/changes/active/`, `.specworks/changes/archive/` and the skills

#### Scenario: AC-CLI-003.2 Inside a project

- **WHEN** `init <path>` runs inside a project (or a module)
- **THEN** the folder is linked as a module, named `parent/child` when nested, with no skills folder of its own

#### Scenario: AC-CLI-003.3 An independent project

- **WHEN** `init --no-link` runs inside a project
- **THEN** the folder isn't linked and is a top level of its own

#### Scenario: AC-CLI-003.5 A theme that cannot apply

- **WHEN** `--diagram-theme` is given for an existing project
- **THEN** init succeeds and says `--diagram-theme not applied`

#### Scenario: AC-CLI-003.6 A folder around an existing module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `init services` runs from the top level
- **THEN** it is refused naming module `billing`, nothing is written (no config, no link), and the workspace still loads

#### Scenario: AC-CLI-003.7 Outside a git repository

- **GIVEN** a folder that is in no git repository
- **WHEN** `init` runs there
- **THEN** it fails saying to run `git init`, and writes nothing (no config, no folder, no skills)

#### Scenario: AC-CLI-003.8 No --dir option

- **WHEN** `init --dir spec` runs
- **THEN** it fails as an unknown option and writes nothing

#### Scenario: AC-CLI-003.9 Asked in a terminal

- **GIVEN** a new project with a `CLAUDE.md`, and `init` running in a terminal without `--tools`
- **WHEN** the question lists `claude` and `copilot` with `claude` as the default, and the answer is `copilot`
- **THEN** skills are installed in `.github/skills/` only and the config saves `tools: [copilot]`

#### Scenario: AC-CLI-003.10 The default answer

- **GIVEN** a new project with a `CLAUDE.md`, and `init` running in a terminal without `--tools`
- **WHEN** the answer is empty
- **THEN** skills are installed for Claude Code and the config saves `tools: [claude]`

#### Scenario: AC-CLI-003.11 No terminal

- **GIVEN** a new project that uses no supported tool
- **WHEN** `init` runs with no terminal (as from CI or an agent)
- **THEN** nothing is asked, skills are installed in `.claude/skills/` only, and the config saves `tools: [claude, copilot]`

#### Scenario: AC-CLI-003.12 tools or a saved choice

- **WHEN** `init --tools copilot` runs in a terminal, or `init` runs again in a project whose config saves tools
- **THEN** nothing is asked; the given tools are installed and saved, or the saved ones are installed

### Requirement: REQ-CLI-004 Overview commands

`context` SHALL show the workspace: root, current module, inherited context,
commands, modules (and missing ones), every capability with its docs path,
prefix and delta path, the changes, and the skills state (`skills`: `current`,
`outdated` with its files, or `none`). When the skills are outdated, it SHALL
also show the hint `skills out of date: run specworks update`. `list` SHALL
list the current module's active changes (every module's with `--all`,
archived ones with `--archived`), flagging an active change that also has an
archived copy. `module list` SHALL show every module with the current one
marked.

#### Scenario: AC-CLI-004.1 Context

- **WHEN** `context` runs
- **THEN** each capability shows its docs path and whether it has a living spec

#### Scenario: AC-CLI-004.2 All modules

- **WHEN** `list` runs with and without `--all`
- **THEN** it lists the current module's changes, or every module's

#### Scenario: AC-CLI-004.3 Archived and leftover changes

- **WHEN** `list --archived` runs, or an active change has an archived copy
- **THEN** archived changes are listed with their date and state, and the leftover copy is flagged with `alsoArchived`

#### Scenario: AC-CLI-004.4 Module tree

- **WHEN** `module list` runs
- **THEN** it lists `(top)` and every module, the current one marked

#### Scenario: AC-CLI-004.5 Skills state

- **GIVEN** installed skills where one skill file was edited
- **WHEN** `context` runs, with and without `--json`
- **THEN** the JSON has `skills` with state `outdated` and that file, and the text output shows `skills out of date: run specworks update`; with current skills, the JSON state is `current` and there is no hint

### Requirement: REQ-CLI-005 Registering modules and capabilities

`module add <path>` SHALL refuse a folder that is not inside the current
project, create the module's `.specworks/config.yml` when it has none,
and link it in the config of the innermost module that contains the folder,
printing the folder's full module name. It SHALL refuse a folder that holds a
module of the workspace, naming that module, before writing anything. `capability add` SHALL refuse an ID prefix, given or derived,
already used by another capability, and SHALL register a capability in the
module `--module` names.

#### Scenario: AC-CLI-005.1 Adding a module

- **WHEN** `module add services/billing` runs
- **THEN** the parent lists it and the module has its `.specworks/config.yml` and changes folder

#### Scenario: AC-CLI-005.2 A folder with an old-style config

- **WHEN** the folder holds an old-style config (a `*.yml` with the `specworks:` line) and no `.specworks/config.yml`
- **THEN** it is refused with the old-layout error naming that file, and nothing is written

#### Scenario: AC-CLI-005.3 A folder outside the project

- **WHEN** the folder is the project itself or outside it
- **THEN** it is refused with `must be a folder inside` the project

#### Scenario: AC-CLI-005.4 A prefix in use

- **WHEN** a capability's prefix (given, or derived from its name) is already used
- **THEN** it is refused naming the capability that uses it, and the config is unchanged

#### Scenario: AC-CLI-005.5 In a module

- **WHEN** `capability add --module billing` runs
- **THEN** the capability is registered in billing's config with its own prefix and paths

#### Scenario: AC-CLI-005.6 A folder inside another module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `module add services/billing/sub` runs from the top level
- **THEN** billing's config lists `sub: sub`, the top level's config is unchanged, and the output names module `billing/sub`

#### Scenario: AC-CLI-005.7 A folder around an existing module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `module add services` runs from the top level
- **THEN** it is refused naming module `billing`, no config is written or changed, and the workspace still loads

### Requirement: REQ-CLI-006 Creating, moving and dropping changes

`new` SHALL create a change in the module nearest the working directory, or in
`--module`, and put it on its own branch: it creates and switches to the
change's branch unless `branch_per_change` or `--no-branch` says to stay
(REQ-CLI-015), and it SHALL fail without
creating the change, naming the reason, when the folder is not inside a git
repository or, when it creates the branch, the branch already exists or HEAD
is detached. `phase <phase>
--change <ref>` SHALL move a change without checking gates, and SHALL refuse
the old argument order with a hint. `abandon` SHALL archive a change without
merging, and requires a reason. `skip-specs` SHALL mark a change as having no
behaviour change, and `--off` removes the mark.

#### Scenario: AC-CLI-006.1 Where a change is created

- **WHEN** `new` runs inside a module's folder, or with `--module`
- **THEN** the change is created in that module; an unknown module is refused

#### Scenario: AC-CLI-006.2 Moving a change

- **WHEN** `phase` names a phase, or an unknown one
- **THEN** the change moves, or the command fails

#### Scenario: AC-CLI-006.3 The change comes with --change

- **WHEN** `phase` is called without `--change` or in the old order
- **THEN** it fails with the corrected command as a hint

#### Scenario: AC-CLI-006.4 Abandoning

- **WHEN** a change is abandoned with a reason
- **THEN** it is archived with its phase and reason, the living spec is untouched, and it leaves the active list; a blank reason is refused

#### Scenario: AC-CLI-006.5 No behaviour change

- **WHEN** `skip-specs` runs, then `skip-specs --off`
- **THEN** the specs artifact is skipped, then required again

#### Scenario: AC-CLI-006.6 The change's branch

- **WHEN** `new` creates a change
- **THEN** the checked-out branch is the change's branch, and the output (and `--json` as `branch`) names it

#### Scenario: AC-CLI-006.7 Staying on the current branch

- **WHEN** `new --no-branch` creates a change
- **THEN** the checked-out branch is unchanged, and `--json` has `branch` null

#### Scenario: AC-CLI-006.8 Nothing is left behind

- **WHEN** `new` runs outside a git repository, or creates the change's branch while that branch already exists or HEAD is detached
- **THEN** it fails naming the reason, and no change folder and no branch are created

#### Scenario: AC-CLI-006.9 Not on the base branch

- **WHEN** `new` runs on a branch other than the base branch
- **THEN** the output (and `--json` as `startedFrom`) names that branch; on the base branch it says nothing

### Requirement: REQ-CLI-007 close

`close` SHALL run validate first and refuse a change that doesn't pass, naming
the phases to go back to. With `--dry-run` it SHALL show the merge plan and
write nothing. `--no-run` SHALL be accepted only with `--dry-run`, because the
real close runs the project's commands before writing.

#### Scenario: AC-CLI-007.1 Dry run

- **WHEN** `close --dry-run` runs
- **THEN** it lists each capability's added, modified and removed requirements, and no file changes

#### Scenario: AC-CLI-007.2 no-run

- **WHEN** `close --no-run` runs without `--dry-run`
- **THEN** it fails and writes nothing; with `--dry-run` it is accepted

#### Scenario: AC-CLI-007.3 Validate fails

- **WHEN** the change doesn't pass validate
- **THEN** close fails with `does not pass validate` and `goBackTo`, and the change stays active

### Requirement: REQ-CLI-008 diagrams

`diagrams` SHALL render the diagrams of a change (`--change`) or of a folder
inside the workspace (`--dir`), or list the themes (`--themes`) with the ones in
use and the d2 found. It requires one of these. `--check` SHALL only report the
diagrams' states and exit 1 when any is missing or stale. A relative `--dir` SHALL be
resolved from the workspace root, wherever the command runs. A folder outside
the workspace, or one that doesn't exist, SHALL be refused.

#### Scenario: AC-CLI-008.1 What to render

- **WHEN** `diagrams` runs with none of `--change`, `--dir` or `--themes`
- **THEN** it fails asking for `--change`

#### Scenario: AC-CLI-008.2 Themes

- **WHEN** `diagrams --themes` runs
- **THEN** it lists every theme with its number and whether it is dark, and the theme and dark theme in use

#### Scenario: AC-CLI-008.3 Check only

- **WHEN** `diagrams --check` runs and a diagram is stale
- **THEN** it exits 1 without rendering

#### Scenario: AC-CLI-008.4 A docs folder

- **WHEN** `diagrams --dir src/auth/docs` runs
- **THEN** that folder's diagrams are rendered and the folder is reported relative to the root

#### Scenario: AC-CLI-008.5 A folder outside the workspace

- **WHEN** `--dir` names a folder outside the workspace
- **THEN** it is refused with `is outside the workspace`

#### Scenario: AC-CLI-008.6 From a subfolder

- **GIVEN** a working directory inside a module of the workspace
- **WHEN** `diagrams --dir src/auth/docs` runs, the folder named relative to the workspace root
- **THEN** that folder's diagrams are rendered

#### Scenario: AC-CLI-008.7 A folder that doesn't exist

- **WHEN** `--dir` names a folder that doesn't exist
- **THEN** it fails with `no folder`, naming the folder relative to the root, and renders nothing

### Requirement: REQ-CLI-009 update

`update` SHALL bring the workspace's skills up to the running CLI. It refreshes
the tools saved in the config (`--tools` overrides them and is saved; with none
saved it uses the tools that have `specworks-…` skills installed, else `auto`,
as `skills` does, and saves them). It SHALL write only the files that differ or
are missing, printing `updated <path>` for each, and remove the stale ones,
printing `removed <path>`. When nothing needs a change, it SHALL write nothing
and print `skills up to date`. Run from a module, it SHALL update the workspace
root's skills.

#### Scenario: AC-CLI-009.1 Outdated skills

- **GIVEN** installed skills where one skill file was edited, another deleted, and a `specworks-propose` folder added
- **WHEN** `update` runs
- **THEN** it prints `updated` for the two files and `removed` for `specworks-propose`, and the skills state is then `current`

#### Scenario: AC-CLI-009.2 Already up to date

- **GIVEN** skills just installed
- **WHEN** `update` runs
- **THEN** it prints `skills up to date` and no installed file is rewritten

#### Scenario: AC-CLI-009.3 Keeps the installed tools

- **GIVEN** a project whose config saves no tools, with only Claude Code skills installed and a `.github/copilot-instructions.md`
- **WHEN** `update` runs
- **THEN** it refreshes the Claude Code skills, writes no Copilot skill or prompt file, and the config then saves `tools: [claude]`

#### Scenario: AC-CLI-009.4 From a module

- **WHEN** `update` runs inside a module's folder
- **THEN** the workspace root's skills are updated and the module gets no skills folder

#### Scenario: AC-CLI-009.5 Both tools, one folder

- **GIVEN** a project whose config saves `tools: [claude, copilot]` and whose skills were just installed
- **WHEN** `update` runs
- **THEN** it prints `skills up to date`, and there is no `specworks-…` skill in `.github/skills/`

### Requirement: REQ-CLI-010 merge

`specworks merge <branch> --change <ref>` SHALL merge the branch for the change
and print whether it merged and which files it resolved; with `--json` it SHALL
print `merged`, `branch` and `resolved`. A failure SHALL be an error value
(`{"error": ...}` under `--json`) with exit code 1, and a folder outside a git
repository SHALL be refused saying so.

#### Scenario: AC-CLI-010.1 A merged branch

- **WHEN** `merge <branch> --change <ref> --json` merges with `tasks.md` resolved
- **THEN** it exits 0 and prints `merged: true`, the branch and `resolved: [<path to tasks.md>]`, the path relative to the workspace root

#### Scenario: AC-CLI-010.2 A refused merge

- **WHEN** the merge is aborted on another conflict
- **THEN** it exits 1 with an error naming the conflicting files

#### Scenario: AC-CLI-010.3 Outside git

- **WHEN** the project is not in a git repository
- **THEN** it exits 1 with an error saying it needs a git repository, and nothing changes

### Requirement: REQ-CLI-011 finding

`specworks finding` SHALL write a change's review findings (REQ-FLOW-016)
through `add <type> <text> --proposal <proposal>`, `decide <id> <decision>`,
`done <id> --in <step> <text>` and `close <id> <text>`, each with `--change`
(the change's ref) and `--json`. Each SHALL print the finding as `specworks
cycle` reads it afterwards (its ID, open or done, and the step it is routed
to) and the path of review.md relative to the workspace root; a refusal
SHALL be an error (`{"error": …}` with exit 1 under `--json`) and change no
file.

#### Scenario: AC-CLI-011.1 The four commands

- **WHEN** `finding add`, `finding decide`, `finding done` and `finding close` run in turn on one change with `--json`
- **THEN** each exits 0 and prints the finding with its ID, state and step, and review.md's path relative to the workspace root

#### Scenario: AC-CLI-011.2 A refusal

- **WHEN** `finding decide R9 "accepted: x"` runs for a finding that does not exist, with `--json`
- **THEN** it prints `{"error": …}` naming R9, exits 1, and review.md is unchanged

### Requirement: REQ-CLI-012 commit

`specworks commit --change <ref>` SHALL commit the change's phase
(REQ-PROJ-024), the active change of that name or, when there is none, the
newest archived one, with `--message` for the subject, `--trailer` (repeatable)
for the trailers and `--json`. It SHALL print the commit's short hash and
subject, the files committed, and the files left out, each relative to the
workspace root; under `--json` it SHALL return them as `commit` (null when
nothing was committed), `committed`, `leftOut` and `alreadyDirty`. A refusal
SHALL be an error (`{"error": …}` with exit 1 under `--json`).

#### Scenario: AC-CLI-012.1 A commit

- **WHEN** `commit --change add-login --trailer "Co-Authored-By: A <a@x>" --json` runs with phase files changed
- **THEN** it exits 0 and returns the commit, the committed and left-out paths relative to the workspace root, and `git log` shows the subject and trailer

#### Scenario: AC-CLI-012.2 Nothing to commit

- **WHEN** `commit --change add-login --json` runs with nothing changed since the record
- **THEN** it exits 0 with `commit` null and an empty `committed`

#### Scenario: AC-CLI-012.3 An unknown change

- **WHEN** `commit --change nope --json` runs
- **THEN** it prints `{"error": …}` naming `nope` and exits 1, when `nope` is neither an active nor an archived change

#### Scenario: AC-CLI-012.4 An archived change

- **GIVEN** a change `add-login` that close has just archived
- **WHEN** `commit --change add-login --json` runs
- **THEN** it exits 0 and returns the commit with the subject `add-login: close`

### Requirement: REQ-CLI-013 config set

`config set <key> [<value>]` SHALL set the key in the config of the current
module, or of the module `--module` names (`branch_per_change` always in the
top level's config, which is the only one read for it), and print the key and the config's
path. The value SHALL come from the argument, or from the file `--file`
names (`-` reads standard input); giving both, or neither, SHALL be refused
before writing. An error SHALL leave the config unchanged.

#### Scenario: AC-CLI-013.1 Setting a command

- **WHEN** `config set commands.test "uv run pytest" --json` runs
- **THEN** it prints the key, the value and the config's path relative to the workspace root, and `specworks context` shows that test command

#### Scenario: AC-CLI-013.2 The context from a file or standard input

- **WHEN** `config set context --file notes.txt` runs, or `config set context --file -` with the text on standard input
- **THEN** the context is that text

#### Scenario: AC-CLI-013.3 Both a value and a file, or neither

- **WHEN** `config set context "text" --file notes.txt` or `config set context` runs
- **THEN** it is refused and the config is unchanged

#### Scenario: AC-CLI-013.4 In a module

- **GIVEN** module `billing`
- **WHEN** `config set commands.test "go test ./..." --module billing` runs from the top level
- **THEN** billing's config has that test command and the top level's config is unchanged

#### Scenario: AC-CLI-013.5 A refused key under --json

- **WHEN** `config set commands.unit pytest --json` runs
- **THEN** it prints `{"error": ...}`, exits 1, and the config is unchanged

#### Scenario: AC-CLI-013.6 The branch setting from inside a module

- **GIVEN** module `billing`
- **WHEN** `config set branch_per_change false --json` runs inside `billing`'s folder, or with `--module billing`
- **THEN** the top level's config has `branch_per_change: false`, billing's config is unchanged, and the output names the top level's config

### Requirement: REQ-CLI-014 Creating a capability's code folder

`capability add` with `--create` SHALL, once the capability is registered,
create its code folder (the path relative to the owning module's root) with
an empty `.gitkeep` when the folder does not exist, and say so in its output:
the `.gitkeep` path relative to the workspace root, or none when nothing was
created. A folder that exists SHALL be left unchanged. A path that exists as
a file SHALL be refused before the config is written. When `capability add`
refuses for any reason, nothing SHALL be created. Without `--create`, no
folder or file SHALL be created.

#### Scenario: AC-CLI-014.1 A missing folder created

- **WHEN** `capability add auth --path src/auth --create --json` runs and `src/auth` does not exist
- **THEN** `src/auth/.gitkeep` exists and is empty, the capability is registered, and the output names `src/auth/.gitkeep` as created

#### Scenario: AC-CLI-014.2 An existing folder left as it is

- **GIVEN** a folder `src/auth` holding a file
- **WHEN** `capability add auth --path src/auth --create --json` runs
- **THEN** the capability is registered, no `.gitkeep` is added, the folder's files are unchanged, and the output names nothing as created

#### Scenario: AC-CLI-014.3 In a module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `capability add invoices --path src/invoices --module billing --create` runs from the top level
- **THEN** `services/billing/src/invoices/.gitkeep` exists and the capability is registered in billing's config

#### Scenario: AC-CLI-014.4 A refused capability creates nothing

- **GIVEN** a capability already using the ID prefix `AUTH`
- **WHEN** `capability add auth2 --path src/auth2 --prefix AUTH --create` runs
- **THEN** it is refused, `src/auth2` does not exist, and the config is unchanged

#### Scenario: AC-CLI-014.5 A path that is a file

- **GIVEN** a file `src/auth`
- **WHEN** `capability add auth --path src/auth --create --json` runs
- **THEN** it prints `{"error": ...}` naming `src/auth`, exits 1, the file is unchanged, and the config is unchanged

#### Scenario: AC-CLI-014.6 Without --create

- **WHEN** `capability add auth --path src/auth` runs and `src/auth` does not exist
- **THEN** the capability is registered and `src/auth` still does not exist

### Requirement: REQ-CLI-015 Staying on the branch

`new` SHALL create the change's branch when the workspace's
`branch_per_change` is true and stay on the current branch when it is false;
`--branch` SHALL create it and `--no-branch` SHALL stay, whatever the
setting. When it stays, the output SHALL name the branch it stayed on (none
with a detached HEAD), and `branch` SHALL be
null.

#### Scenario: AC-CLI-015.1 The setting is false

- **GIVEN** `branch_per_change: false` and HEAD on `work`
- **WHEN** `new add-login --json` runs
- **THEN** HEAD is still on `work`, no branch `add-login` exists, and the output has `branch` null and `stayedOn` `work`

#### Scenario: AC-CLI-015.2 branch overrides false

- **GIVEN** `branch_per_change: false`
- **WHEN** `new add-login --branch` runs
- **THEN** the branch `add-login` is created and checked out

#### Scenario: AC-CLI-015.3 no-branch overrides true

- **GIVEN** no `branch_per_change` in the config
- **WHEN** `new add-login --no-branch --json` runs
- **THEN** HEAD is still on its branch, and the output has `branch` null and `stayedOn` naming it

#### Scenario: AC-CLI-015.4 No setting, no flag

- **GIVEN** no `branch_per_change` in the config
- **WHEN** `new add-login --json` runs
- **THEN** the branch `add-login` is created and checked out, and `stayedOn` is null

#### Scenario: AC-CLI-015.5 The text output

- **GIVEN** `branch_per_change: false` and HEAD on `work`
- **WHEN** `new add-login` runs
- **THEN** the output has a line `stayed on work`

#### Scenario: AC-CLI-015.6 Staying on a detached HEAD

- **GIVEN** `branch_per_change: false` and a detached HEAD
- **WHEN** `new add-login --json` runs
- **THEN** the change is created, HEAD is still detached, and the output has `branch` and `stayedOn` null
