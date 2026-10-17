"""Workflow commands: gates, starting a phase, review, cycle, validate, close and the project's own commands."""

from __future__ import annotations

import json

import typer

from ..core.changes import PHASES
from ..core.runner import cached_run
from ..specs.merge import archive_target, close_change, plan_merge
from ..specs.trace import GAP_LABELS, Analysis
from ..workflow.checks import Check, GateContext, passed
from ..workflow.cycle import next_cycle
from ..workflow.gate import GATES, run_gate, start_phase
from ..workflow.review import review_change
from ..workflow.validate import GROUPS, summary, validate_change
from .app import app
from .output import ChangeOpt, FreshOpt, JsonOpt, change_dict, emit, fail, require_change, workspace


@app.command()
def gate(
    phase: str = typer.Argument(..., help=f"Phase to check: {', '.join(GATES)}."),
    change: str = ChangeOpt,
    no_run: bool = typer.Option(False, "--no-run", help="design/code/review: do not run the project's commands (reported as a warning)."),
    base: str | None = typer.Option(None, "--base", help="review: branch to diff against (default: origin's default branch)."),
    allow_open: bool = typer.Option(
        False, "--allow-open", help="review: open findings do not fail the gate (inside /specworks-build they start the next cycle)."
    ),
    fresh: bool = FreshOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Check whether a change has finished a phase (exit 1 if a blocking check fails)."""
    ws, mod, ch = require_change(change, as_json)
    ok, checks = run_gate(GateContext(ws, mod, ch, run_tests=not no_run, base=base, allow_open=allow_open, reuse_runs=not fresh), phase)
    data = {**change_dict(ws, mod, ch), "gate": phase, "passed": ok, "checks": [c.to_dict() for c in checks]}
    emit(data, as_json, "\n".join(_check_lines(checks) + [f"gate {phase}: {'passed' if ok else 'NOT passed'}"]))
    if not ok:
        raise typer.Exit(1)


def _check_lines(checks: list[Check]) -> list[str]:
    lines = []
    for c in checks:
        lines.append(f"[{c.mark}] {c.name}" + (f"  -> {c.fix}" if c.fix and not c.ok else ""))
        lines += [f"         {d}" for d in c.details]
    return lines


@app.command()
def start(
    phase: str = typer.Argument(..., help=f"Phase to start: {', '.join(p for p in PHASES if p != 'done')}."),
    change: str = ChangeOpt,
    no_run: bool = typer.Option(False, "--no-run", help="Do not run the project's commands in the gates (reported as a warning)."),
    base: str | None = typer.Option(None, "--base", help="Branch the review and validate gates diff against (default: origin's default branch)."),
    fresh: bool = FreshOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Move a change to a phase once the gates it depends on pass (exit 1, phase unchanged, if one fails).

    Moving forward, every phase left behind must pass its gate; going back to a
    phase (or re-entering it) needs the gate of the phase just before it.
    """
    ws, mod, ch = require_change(change, as_json)
    before = ch.phase
    started, gates = start_phase(GateContext(ws, mod, ch, run_tests=not no_run, base=base, reuse_runs=not fresh), phase)
    data = {
        **change_dict(ws, mod, ch),
        "from": before,
        "started": started,
        "gates": [{"gate": g, "passed": passed(checks), "checks": [c.to_dict() for c in checks]} for g, checks in gates],
    }
    lines = []
    for g, checks in gates:
        lines += [f"gate {g}:"] + _check_lines(checks)
    ref = mod.qualify(ch.name)
    lines.append(f"{ref}: phase {before} → {phase}" if started else f"{ref}: stays in {before}; gate {gates[-1][0]} NOT passed")
    emit(data, as_json, "\n".join(lines))
    if not started:
        raise typer.Exit(1)


@app.command()
def review(
    change: str = ChangeOpt,
    base: str | None = typer.Option(None, "--base", help="Branch to diff against (default: origin's default branch)."),
    as_json: bool = JsonOpt,
) -> None:
    """Drift candidates between a change's specs and its code, in both directions."""
    ws, mod, ch = require_change(change, as_json)
    report = review_change(Analysis(ws, ch), base)
    data = {**change_dict(ws, mod, ch), **report.to_dict()}
    labels = {
        **GAP_LABELS,
        "unknownTags": "tags to unknown IDs",
        "untracedSource": "changed code files without `@req` tags",
        "untracedTests": "changed test files without `@ac` tags",
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
    fresh: bool = FreshOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Final read-only check before close (validate phase): completeness, correctness, coherence (exit 1 on FAIL)."""
    ws, mod, ch = require_change(change, as_json)
    checks = validate_change(GateContext(ws, mod, ch, run_tests=not no_run, base=base, reuse_runs=not fresh))
    result = summary(checks)
    data = {**change_dict(ws, mod, ch), **result, "checks": [c.to_dict() for c in checks]}
    lines = []
    for group in GROUPS:
        counts = result["groups"][group]
        lines.append(f"{group.capitalize()} ({counts['passed']}/{counts['total']})")
        for c in (c for c in checks if c.group == group):
            lines.append(f"  [{c.mark}] {c.name}" + ("" if c.ok else f"  -> {c.fix}"))
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
    no_run: bool = typer.Option(False, "--no-run", help="With --dry-run: validate without running test/lint/typecheck."),
    as_json: bool = JsonOpt,
) -> None:
    """Merge the change's delta specs into the living specs, update requirements.md, and archive the change."""
    if no_run and not dry_run:
        fail("--no-run only goes with --dry-run: the real close runs test, lint and typecheck before writing anything", as_json)
    ws, mod, ch = require_change(change, as_json)
    ref = mod.qualify(ch.name)
    # The real close is the last check before the living docs change: it runs the commands, never reuses a result.
    ctx = GateContext(ws, mod, ch, run_tests=not no_run, base=base, reuse_runs=dry_run)
    result = summary(validate_change(ctx))
    if result["verdict"] != "PASS":
        fail(
            f"{ref} does not pass validate ({result['critical']} critical); run `specworks validate --change {ref}`",
            as_json,
            goBackTo=result["goBackTo"],
        )
    merges = plan_merge(ws, ch, ctx.analysis.specs, ref)
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
    result = cached_run(ws, mod, key, reuse=False, capture=as_json)
    if as_json:
        typer.echo(
            json.dumps(
                {"key": key, "command": result.command, "cwd": result.cwd, "exitCode": result.exit_code, "ok": result.ok, "tail": result.tail()},
                indent=2,
            )
        )
    raise typer.Exit(result.exit_code)
