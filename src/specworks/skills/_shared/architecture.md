**The architecture**: the top level and every module have one architecture,
`<docsPath>/architecture.md` (`docsPath` of the module in `specworks context --json`),
with one block diagram,
`<docsPath>/diagrams/architecture-blocks.d2`,
rendered with `specworks diagrams --dir "<docsPath>"`. It is the picture of the
whole module that people and the phases read first; the list of capabilities,
with their paths, stays in `specworks context`. Its sections:
```markdown
# Architecture: <project or module>

## Overview
<what the system is for and how it is put together, in a few lines>

## Capabilities and how they interact
<one line per capability: what it uses from or gives to the others; each
module is one block, linking to its own `docs/architecture.md`>
<the block diagram `diagrams/architecture-blocks.d2`, embedded>

## Architectural decisions
<each decision that spans capabilities: what, why, and the change that made it `(<change>)`>

## Glossary
<each term with one meaning, under one name>
```
Keep it to about 150 lines: merge or drop entries rather than grow it.
At every close, check it against the change.
Update it when the change adds or removes a capability, changes what flows between capabilities, adds a decision that spans capabilities, or adds a term; otherwise leave it as it is.
When it is missing, write it now, before `specworks close`.
