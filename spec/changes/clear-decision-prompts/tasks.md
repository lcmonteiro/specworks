# Tasks: clear-decision-prompts

## 1. Shared rule

- [x] 1.1 Write `src/specworks/skills/_shared/asking-the-user.md` (the yes/no and numbered-options forms with one "(recommended)" and its reason, nothing after the question, one decision at a time, phase ends as a choice of next steps); verify by reading it
- [x] 1.2 Include it (`<!-- specworks:include asking-the-user -->`) in every packaged skill, after `running-cli`; verify `specworks skills` renders it in each installed copy and `tests/test_skills.py` passes

## 2. Decision points

- [x] 2.1 adopt and baseline: reword the folder name, modules, commands, context, capability table, capability choice, and requirements and bug list as yes/no or numbered options; verify by reading each stop
- [x] 2.2 refine and specify: reword init, continue-a-change, name and module, "Ready to record?", scope questions and the requirements table; verify by reading each stop
- [x] 2.3 design, test and code: reword the API list, the test command and code's "Pause and ask"; verify by reading each stop
- [x] 2.4 review, build and close (done follows close): reword each finding's proposal, "Start cycle N?", registering a capability and "Merge and archive?"; verify by reading each stop

## 3. Phase ends

- [x] 3.1 Turn every "When you are ready, run ..." and final report into numbered next steps with one "(recommended)" and "stop here" (refine, specify, design, test, code, review, build, validate, close, done, adopt, baseline); verify by reading each skill's last step

## 4. Installed copies and checks

- [x] 4.1 Refresh the installed copies with `specworks skills`; verify `git diff` shows only skill files changed
- [x] 4.2 Run `specworks run test` and `specworks run lint`; verify both pass
