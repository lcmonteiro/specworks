# Design: clear-decision-prompts

## Interfaces

None: the change edits the text of the packaged skills and adds one shared
include (`src/specworks/skills/_shared/asking-the-user.md`), rendered by the
existing `<!-- specworks:include <name> -->` mechanism. No API, CLI surface or
data shape changes.
