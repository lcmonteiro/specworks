# Design: share-skill-rules

## Context

`read_skill` (`src/specworks/tools/skills.py`) replaces each line
`<!-- specworks:include <name> -->` with `_shared/<name>.md`, verbatim.
`expected_skills` fills in every skill before `install_skills` writes any.
See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- Parameters on includes, checked both ways (unfilled, unused).
- "Back from review" and "start implement / gate fails" written once.
- Every installed skill identical, byte for byte, to what this version
  installs today.

**Non-Goals:**
- Other rules (see proposal.md, Out of Scope); conditionals or loops in
  shared files.

## Decisions

### The include line

`INCLUDE_RE` becomes
`^<!-- specworks:include (?P<name>[a-z0-9-]+)(?P<params>(?: [a-z_]+=(?:"[^"]*"|[^\s"]+))*) -->\n`.
A parameter is `key=value` (no spaces, no quotes) or `key="value"` (any text
but `"`, empty allowed). A key given twice is an error. Serves:
REQ-INTEG-007.

### Filling in

`fill_includes(text, skill, shared)` replaces each include with
`shared(name)` after replacing every `{{key}}` by its value. Then:
- a `{{word}}` left in the result of that include is unfilled:
  `skill <skill>: include <name> leaves {{<key>}} unfilled`;
- a given key with no `{{key}}` in the shared file is unused:
  `skill <skill>: include <name> does not use <key>`;
- a key given twice: `skill <skill>: include <name> gives <key> twice`.

Each raises `ToolError`. An include with no parameters and no `{{` is copied
as it is. `read_skill(name)` calls `fill_includes` with the packaged
`_shared` folder. `expected_skills` already fills in every skill before
`install_skills` writes one, so a failure writes nothing; `specworks skills`
reports the `ToolError` as its other errors (exit 1, `{"error": ...}` under
`--json`). Serves: REQ-INTEG-007.

`write_skills` (`src/specworks/cli/project.py`) and `update_skills` remove
stale skills before they fill any skill in, so a failing include would still
delete a stale specworks skill folder, against AC-INTEG-007.6 ("no skill
folder is written or changed"). Both fill every skill in first
(`expected_skills(tools)`), then remove the stale ones, then write: a
failure changes nothing on disk. Signatures stay as they are. Serves:
REQ-INTEG-007.

### The shared files

- `_shared/back-from-review.md`: the "Back from review" paragraph of
  design, test and code, with `{{phases}}` (`` `design` ``, `` `test` ``,
  `` `code` or `implement` ``), `{{note}}` (empty for design and code; the
  test skill's sentence on findings routed to `implement`, with its leading
  space) and `{{in}}` (`design`, `test`, `code, or implement for a finding
  routed to both halves`).
- `_shared/start-implement.md`: from `specworks start implement --change`
  to "themselves fail)." in test and code, then `{{note}}` and a final
  newline, as `back-from-review.md` ends. `{{other}}` is `code` in the test
  skill and `test` in the code skill; `{{note}}` is the test skill's extra
  sentence with its leading space
  (`note=" Tests built on an undecided API test the wrong thing."`) and empty
  in the code skill (`note=""`). Neither skill keeps an extra line after the
  include, so the filled-in text does not depend on the shared file having
  no final newline (review R2).

The include line sits where the text was; values are quoted where they hold
spaces or backticks. Not a requirement (skills have no capability); checked
by the installed copies staying unchanged.

### Pinned wording

The test half asserts these exactly:
- error fragments: `leaves {{phase}} unfilled`, `does not use colour`,
  `gives`, and the skill name and shared file name in each;
- after the skill moves, `uv run specworks skills` changes no file under
  `.claude/skills/`, and the three skills' `SKILL.md` contain
  `<!-- specworks:include back-from-review` (design, test, code) and
  `<!-- specworks:include start-implement` (test, code).

## Interfaces

Agreed with the user (option 1: fill in every skill before removing or writing any)

- `src/specworks/tools/skills.py`: `INCLUDE_RE` (extended): the include line
  with optional parameters, groups `name` and `params` (REQ-INTEG-007)
- `src/specworks/tools/skills.py`:
  `fill_includes(text: str, skill: str, shared: Callable[[str], str]) -> str`
  (new): `text` is a skill's SKILL.md, `skill` its name (for the errors),
  `shared(name)` returns the text of the shared file `name`; raises `ToolError` for an
  unfilled `{{key}}`, an unused key or a key given twice, each message
  naming the skill, the include and the key (REQ-INTEG-007)
- `src/specworks/tools/skills.py`: `read_skill(name: str) -> str`
  (unchanged signature): fills in through `fill_includes` with the packaged
  `_shared` folder, so it may now raise `ToolError` (REQ-INTEG-007)
- `src/specworks/tools/skills.py`: `update_skills(root, tools)` and
  `src/specworks/cli/project.py`: `write_skills(ws, tools)` (unchanged
  signatures): fill in every skill before removing or writing any
  (REQ-INTEG-007)
- `src/specworks/tools/skills.py`: `ToolError` (unchanged class; its
  docstring widens to "unknown tool ids, or a skill that cannot be filled
  in")

Not breaking: no packaged skill has parameters yet, and an include without
parameters is filled in as today. AC-INTEG-007.6 is reached by replacing
`specworks.tools.skills.read_skill` (or `fill_includes`) with one that
raises, as `expected_skills` calls it by its module name; no test-only hook
is added.

The stub (task 1.1): `fill_includes` with its real signature and docstring
fills in includes as today, ignoring parameters and raising nothing, and
`read_skill` calls it; the existing suite stays green, and the tests for
parameters and the three errors fail on it.

## Diagrams

No structural change: one function in an existing module.

## Risks / Trade-offs

- [a value needs a `"`] -> not supported; the shared text keeps it.
- [the move changes a skill's text by a space or a newline] -> the check
  that `specworks skills` leaves `.claude/skills/` unchanged.

## Open Questions

None.
