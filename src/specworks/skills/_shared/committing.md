**Committing**: once this phase's gate has passed (a phase with no gate: once its
artifact is written), and before the closing question, commit its work:
- stage explicit paths only: the change folder and the files this phase wrote
  or changed; never `git add -A`, and never a whole-folder add;
- name any unrelated dirty or untracked file in the report and leave it out of
  the commit;
- the message follows the project's commit convention when one exists (a commit
  skill, `CLAUDE.md`, `.github/copilot-instructions.md`, the project `context`),
  otherwise `<ref>: <phase>`, with the ref and the phase in the body or a
  trailer when the convention allows;
- never push: only `/specworks-close` and `/specworks-done` offer that.
