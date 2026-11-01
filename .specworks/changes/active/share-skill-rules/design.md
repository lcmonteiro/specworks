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

### The shared files

- `_shared/back-from-review.md`: the "Back from review" paragraph of
  design, test and code, with `{{phases}}` (`` `design` ``, `` `test` ``,
  `` `code` or `implement` ``), `{{note}}` (empty for design and code; the
  test skill's sentence on findings routed to `implement`, with its leading
  space) and `{{in}}` (`design`, `test`, `code, or implement for a finding
  routed to both halves`).
- `_shared/start-implement.md`: from `specworks start implement --change`
  to "themselves fail)." in test and code, with `{{other}}` (`code` in the
  test skill, `test` in the code skill). The test skill keeps its extra
  sentence ("Tests built on an undecided API test the wrong thing.") on the
  line after the include, in its own text.

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

- `src/specworks/tools/skills.py`: `INCLUDE_RE` (extended);
  `fill_includes(text: str, skill: str, shared: Callable[[str], str]) -> str`,
  raising `ToolError` (REQ-INTEG-007); `read_skill(name)` unchanged in
  signature.

## Diagrams

No structural change: one function in an existing module.

## Risks / Trade-offs

- [a value needs a `"`] -> not supported; the shared text keeps it.
- [the move changes a skill's text by a space or a newline] -> the check
  that `specworks skills` leaves `.claude/skills/` unchanged.

## Open Questions

None.
