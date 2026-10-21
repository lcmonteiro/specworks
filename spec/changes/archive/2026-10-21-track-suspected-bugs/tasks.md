# Tasks: track-suspected-bugs

## 1. Baseline skill

- [x] 1.1 In `src/specworks/skills/specworks-baseline/SKILL.md`, step 3: record each suspected bug's evidence (where it shows, observed versus expected); verify by reading the step
- [x] 1.2 Step 4: after the user confirms, create `fix-<short-name>` for each confirmed bug (`specworks new`, `--module` for another module) and write its `refinement.md` from the `refinement` instructions (Problem and Context from the evidence, naming the baseline; Options and Recommendation "Pending"); name each change ref in the proposal's Out of Scope; verify by reading the step
- [x] 1.3 Step 9: when no capability is left without a living spec, list the waiting bug changes (`specworks list --json`, phase refine) and hand over to the loop refine → specify → build → done for each, with `specworks abandon` for one that is not a bug; verify by reading the step
- [x] 1.4 Boundary and guardrails: the bug change and its `refinement.md` are the only writing outside the baseline's change, and no bug is fixed; verify by reading them

## 2. Adopt skill

- [x] 2.1 In `src/specworks/skills/specworks-adopt/SKILL.md`, add the closing "for each suspected bug" loop to the overview and to the step 7 report; verify by reading them

## 3. Installed copies and checks

- [x] 3.1 Refresh `.claude/skills` and `.github/skills` with `specworks skills`; verify `git diff` shows only the two skills changed
- [x] 3.2 Run `specworks run test` and `specworks run lint`; verify both pass (the skill rendering tests included)
