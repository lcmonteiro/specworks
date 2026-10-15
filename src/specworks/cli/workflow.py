"""Workflow commands: gates, review, cycle, validate, close and the project's own commands."""

from __future__ import annotations

import json

import typer

from ..core.runner import run_command
from ..specs.check import check_change
from ..specs.merge import archive_target, close_change, plan_merge
from ..workflow.cycle import next_cycle
from ..workflow.gate import GATES, GateContext, run_gate
from ..workflow.review import review_change
from ..workflow.validate import GROUPS, summary, validate_change
from .app import app
from .output import ChangeOpt, JsonOpt, change_dict, emit, fail, require_change, workspace


@app.command()
def gate(
    phase: str = typer.Argument(..., help=f"Phase to check: {', '.join(GATES)}."),
    change: str = ChangeOpt,
    no_run: bool = typer.Option(False, "--no-run", help="design/code/review: do not run the project's commands (reported as a warning)."),
    base: str | None = typer.Option(None, "--base", help="review: branch to diff against (default: origin's default branch)."),
    allow_open: bool = typer.Option(
        False, "--allow-open", help="review: open findings do not fail the gate (inside /specworks-build they start the next cycle)."
    ),
    as_json: bool = JsonOpt,
) -> None:
    """Check whether a change has finished a phase (exit 1 if a blocking check fails)."""
    ws, mod, ch = require_change(change, as_json)
    passed, checks = run_gate(GateContext(ws, mod, ch, run_tests=not no_run, base=base, allow_open=allow_open), phase)
    data = {**change_dict(ws, mod, ch), "gate": phase, "passed": passed, "checks": [c.to_dict() for c in checks]}
    lines = []
    for c in checks:
        mark = "ok  " if c.ok else ("FAIL" if c.blocking else "warn")
        lines.append(f"[{mark}] {c.name}")
        lines += [f"         {d}" for d in c.details]
    lines.append(f"gate {phase}: {'passed' if passed else 'NOT passed'}")
    emit(data, as_json, "\n".join(lines))
    if not passed:
        raise typer.Exit(1)


@app.command()
def review(
    change: str = ChangeOpt,
    base: str | None = typer.Option(None, "--base", help="Branch to diff against (default: origin's default branch)."),
    as_json: bool = JsonOpt,
) -> None:
    """Drift candidates between a change's specs and its code, in both directions."""
    ws, mod, ch = require_change(change, as_json)
    _, report = review_change(ws, ch, base)
    data = {**change_dict(ws, mod, ch), **report.to_dict()}
    labels = {
        "reqWithoutCode": "requirements without code (@req)",
        "acWithoutTests": "acceptance criteria without tests (@ac)",
        "removedStillTagged": "removed requirements still tagged",
        "unknownTags": "tags to unknown IDs",
        "untracedSource": "changed code files without @req tags",
        "untracedTests": "changed test files without @ac tags",
    }
    lines = [f"base: {report.base or '-'}"] + ([f"note: {report.note}"] if report.note else [])
    lines += [f"spec error: {e}" for e in report.spec_errors]
    for key, items in data["findings"].items():
        lines.append(f"{labels[key]}: {len(items)}")
        lines += [f"  {item}" for item in items]
    lines.append(f"{data['findingCount']} drift candidates")
    emit(data, as_json, "\n".join(lines))


@app.command()
def cycle(
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """After a review: where the next design → test → code → review cycle starts, from review.md's open findings."""
    ws, mod, ch = require_change(change, as_json)
    result = next_cycle(ch)
    data = {**change_dict(ws, mod, ch), **result}
    if not result["reviewed"]:
        lines = ["not reviewed yet: no review.md (run /specworks-review)"]
    elif not result["open"]:
        lines = ["no open findings: the build is done; next is /specworks-validate"]
    else:
        lines = [f"{f['id']} {f['type'] or '?'} -> {f['phase']}" for f in result["open"]]
        if result["handOver"]:
            lines.append(f"a spec finding: stop the build and run {result['handOver']} {mod.qualify(ch.name)}")
        else:
            lines.append(f"next cycle: {' -> '.join(result['phases'])}")
    emit(data, as_json, "\n".join(lines))


@app.command("validate")
def validate_cmd(
    change: str = ChangeOpt,
    base: str | None = typer.Option(None, "--base", help="Branch to diff against (default: origin's default branch)."),
    no_run: bool = typer.Option(False, "--no-run", help="Do not run test/lint/typecheck (reported as warnings)."),
    as_json: bool = JsonOpt,
) -> None:
    """Final read-only check before close (validate phase): completeness, correctness, coherence (exit 1 on FAIL)."""
    ws, mod, ch = require_change(change, as_json)
    checks = validate_change(ws, mod, ch, run=not no_run, base=base)
    result = summary(checks)
    data = {**change_dict(ws, mod, ch), **result, "checks": [c.to_dict() for c in checks]}
    lines = []
    for group in GROUPS:
        counts = result["groups"][group]
        lines.append(f"{group.capitalize()} ({counts['passed']}/{counts['total']})")
        for c in (c for c in checks if c.group == group):
            mark = "ok  " if c.ok else ("FAIL" if c.blocking else "warn")
            lines.append(f"  [{mark}] {c.name}" + ("" if c.ok else f"  -> {c.fix}"))
            lines += [f"           {d}" for d in c.details if not c.ok or d.startswith("$ ")]
    lines.append(f"{mod.qualify(ch.name)}: {result['verdict']} ({result['critical']} critical, {result['warnings']} warnings)")
    if result["goBackTo"]:
        lines.append(f"go back to: {', '.join(result['goBackTo'])}")
    emit(data, as_json, "\n".join(lines))
    if result["verdict"] != "PASS":
        raise typer.Exit(1)


@app.command()
def close(
    change: str = ChangeOpt,
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be merged and archived; write nothing."),
    base: str | None = typer.Option(None, "--base", help="Branch to diff against for validate (default: origin's default branch)."),
    no_run: bool = typer.Option(False, "--no-run", help="Validate without running test/lint/typecheck."),
    as_json: bool = JsonOpt,
) -> None:
    """Merge the change's delta specs into the living specs, update requirements.md, and archive the change."""
    ws, mod, ch = require_change(change, as_json)
    ref = mod.qualify(ch.name)
    result = summary(validate_change(ws, mod, ch, run=not no_run, base=base))
    if result["verdict"] != "PASS":
        fail(
            f"{ref} does not pass validate ({result['critical']} critical); run `specworks validate --change {ref}`",
            as_json,
            goBackTo=result["goBackTo"],
        )
    specs, _ = check_change(ws, ch)
    merges = plan_merge(ws, ch, specs, ref)
    archive_target(ch, mod.config.archive_path)
    data = {**change_dict(ws, mod, ch), "dryRun": dry_run, "merges": [m.to_dict(ws) for m in merges], "archivedTo": None}
    lines = [f"{'would merge' if dry_run else 'merged'} {m.cap.ref} -> {ws.rel(m.spec_path)}{' (new)' if m.created else ''}: {m.summary()}" for m in merges]
    lines = lines or ["no delta specs to merge (skip_specs)"]
    if not dry_run:
        try:
            target = close_change(merges, ch, mod.config.archive_path)
        except OSError as exc:
            fail(str(exc), as_json)
        data["archivedTo"] = ws.rel(target)
        data["phase"] = "done"
        lines.append(f"archived -> {data['archivedTo']}")
    emit(data, as_json, "\n".join(lines))


@app.command()
def run(
    key: str = typer.Argument(..., help="Command to run: test, lint, typecheck, build or format."),
    change: str | None = typer.Option(None, "--change", "-c", help="Run in the module owning this change."),
    as_json: bool = JsonOpt,
) -> None:
    """Run one of the project's configured commands in the right module folder (exit code passes through)."""
    if change:
        ws, mod, _ = require_change(change, as_json)
    else:
        ws = workspace(as_json)
        mod = ws.current
    result = run_command(ws, mod, key, capture=as_json)
    if as_json:
        typer.echo(
            json.dumps(
                {"key": key, "command": result.command, "cwd": result.cwd, "exitCode": result.exit_code, "ok": result.ok, "tail": result.tail()},
                indent=2,
            )
        )
    raise typer.Exit(result.exit_code)
