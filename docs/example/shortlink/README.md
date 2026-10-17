# shortlink: the example project of the guide

The project [`docs/guide.md`](../../guide.md) builds, as it is at the end of the
guide: two closed changes and one abandoned one.

| Where | What |
|---|---|
| `spec.yml` | the config: context, commands, the `links` capability |
| `src/shortlink/store.py`, `errors.py` | the code, tagged `@req` |
| `tests/test_store.py` | the tests, tagged `@ac` |
| `src/shortlink/docs/` | the living docs `specworks close` and `/specworks-close` wrote: `spec.md`, `requirements.md`, `design.md`, `diagrams/` |
| `spec/changes/archive/2026-10-17-add-short-links/` | change 1, every artifact: refinement, proposal, delta spec, design, diagram, tasks, traceability, review |
| `spec/changes/archive/2026-10-17-add-link-expiry/` | change 2: a MODIFIED requirement |
| `spec/changes/archive/2026-10-17-add-custom-codes/` | an abandoned change |

`pytest.ini` only makes this folder its own pytest root inside the specworks
repository. To try the commands, from this folder:

```bash
specworks spec show links
specworks list --archived
specworks status --change add-short-links
specworks run test
```
