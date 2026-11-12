"""Workflow commands: gates, starting a phase, review, cycle, merging a half's branch, validate, close and the project's own commands."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path

import typer

from specworks.cli.app import app, finding_app
from specworks.cli.output import ChangeOpt, FreshOpt, JsonOpt, change_dict, emit, fail, require_change, workspace
from specworks.cli.telemetry import record
from specworks.core.changes import PHASES, Change
from specworks.core.runner import cached_run
from specworks.core.workspace import Workspace
from specworks.specs.merge import archive_target, close_change, plan_merge
from specworks.specs.trace import GAP_LABELS, Analysis
from specworks.workflow.artifacts import check_artifact_for, check_artifacts
from specworks.workflow.checks import Check, GateContext, passed
from specworks.workflow.cycle import next_cycle
from specworks.workflow.findings import Finding, FindingError, add_finding, close_finding, decide_finding, mark_finding_done
from specworks.workflow.gate import GATES, run_gate, start_phase
from specworks.workflow.merge import BranchMergeError, merge_branch
from specworks.workflow.review import review_change
from specworks.workflow.validate import GROUPS, summary, validate_change, write_validation


@app.command()
def gate(
    phase: str = typer.Argument(..., help=f"Gate to check: {', '.join(GATES)} (test and code are the halves of implement; implement runs both)."),
    change: str = ChangeOpt,
    no_run: bool = typer.Option(False, "--no-run", help="design/code/implement/review: do not run the project's commands (reported as a warning)."),
    base: str | None = typer.Option(None, "--base", help="review: branch to diff against (default: origin's default branch)."),
    allow_open: bool = typer.Option(
        False, "--allow-open", help="review: open findings do not fail the gate (inside /specworks-build they start the next cycle)."
    ),
    fresh: bool = FreshOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Check whether a change has finished a phase (exit 1 if a blocking check fails)."""
    ws, mod, ch = require_change(change, as_json)
    started = time.monotonic()
    ok, checks = run_gate(GateContext(ws, mod, ch, run_tests=not no_run, base=base, allow_open=allow_open, reuse_runs=not fresh), phase)
    data = {**change_dict(ws, mod, ch), "gate": phase, "passed": ok, "checks": [c.to_dict() for c in checks]}
    record(ws, mod, ch, "gate", started, gate=phase, passed=ok, failed=[c.name for c in checks if c.blocking and not c.ok])
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
    phase: str = typer.Argument(..., help=f"Phase to start: {', '.join(p for p in PHASES if p != 'done')} (implement covers test and code)."),
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
    began = time.monotonic()
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
    record(ws, mod, ch, "start", began, to=phase, started=started)
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
        "deletedFiles": "deleted code and test files",
    }
    lines = [f"base: {report.since or report.base or '-'}"] + ([f"note: {report.note}"] if report.note else [])
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
    """After a review or a validate: the steps the next build cycle runs (design, test, code, review), where it starts, and the change's next state, from the open findings of every check artifact.

    Implements REQ-FLOW-012.
    """
    ws, mod, ch = require_change(change, as_json)
    started = time.monotonic()
    result = next_cycle(ch)
    data = {**change_dict(ws, mod, ch), **result}
    if result["open"]:
        lines = [f"{f['id']} {f['type'] or '?'} -> {f['phase']}" for f in result["open"]]
        if result["handOver"]:
            lines.append(f"a spec finding: stop the build and run {result['handOver']} {mod.qualify(ch.name)}")
        elif result["phases"]:
            lines.append(f"next cycle: {' -> '.join(result['phases'])}")
        else:
            lines.append("no build cycle: the open findings wait for /specworks-validate to confirm them")
    elif not result["reviewed"]:
        lines = ["not reviewed yet: no review.md (run /specworks-review)"]
    else:
        lines = ["no open findings: the build is done; next is /specworks-validate"]
    if result["next"]:
        lines.append(f"next: {result['next']}")
    record(ws, mod, ch, "cycle", started, phases=list(result["phases"]), open=len(result["open"]))
    emit(data, as_json, "\n".join(lines))


# @req REQ-CLI-010
@app.command()
def merge(
    branch: str = typer.Argument(..., help="Branch to merge into the current checkout (in /specworks-build, the test half's worktree branch)."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Merge a branch for a change, resolving its tasks.md (every tick kept) and traceability.md (regenerated); abort on any other conflict.

    Implements REQ-CLI-010.
    """
    ws, mod, ch = require_change(change, as_json)
    try:
        result = merge_branch(ws, mod, ch, branch)
    except BranchMergeError as exc:
        fail(str(exc), as_json, files=[_rel(ws, f) for f in exc.files])
    data = {**change_dict(ws, mod, ch), **result.to_dict(ws)}
    if not result.merged:
        lines = [f"{branch}: already up to date, nothing to merge"]
    else:
        lines = [f"resolved {path}" for path in data["resolved"]] + [f"merged {branch} into the current checkout"]
    emit(data, as_json, "\n".join(lines))


# @req REQ-CLI-011
@finding_app.command("add")
def finding_add(
    kind: str = typer.Argument(..., metavar="TYPE", help="The finding's type: spec-gap, design-gap, test-gap, code-gap, tag, quality or question."),
    text: str = typer.Argument(..., help="What the finding is."),
    proposal: str = typer.Option(..., "--proposal", help="The change it proposes."),
    artifact: str = typer.Option(
        "review", "--artifact", help="The check artifact it goes to: review (review.md), validation (validation.md) or inspection (inspection.md)."
    ),
    suggestion: str | None = typer.Option(None, "--suggestion", metavar="FILE", help="A file (or - for standard input) whose text goes under the finding as its Suggestion."),
    lang: str = typer.Option("text", "--lang", help="The language the Suggestion's fence is marked with, e.g. diff or python."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Add an open finding with the next free ID and its Proposal to a check artifact (review.md by default), created from its template when missing.

    Implements REQ-CLI-011.
    """
    if suggestion is not None:
        raise NotImplementedError("finding add --suggestion")
    _write_finding(change, as_json, "add", lambda ch: add_finding(ch, kind, text, proposal, artifact=artifact))


# @req REQ-CLI-011
@finding_app.command("decide")
def finding_decide(
    finding_id: str = typer.Argument(..., metavar="ID", help="The finding's ID, e.g. R1."),
    decision: str = typer.Argument(..., help="'back to <step>: ...' (specify, design, implement, test or code), 'back to design only: ...' (design, then review) or 'accepted: ...'."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Write a finding's Decision, replacing the one it has; 'accepted' ticks it.

    Implements REQ-CLI-011.
    """
    _write_finding(change, as_json, "decide", lambda ch: decide_finding(ch, finding_id, decision))


# @req REQ-CLI-011
@finding_app.command("done")
def finding_done(
    finding_id: str = typer.Argument(..., metavar="ID", help="The finding's ID, e.g. R1."),
    text: str = typer.Argument(..., help="What the step changed."),
    step: str = typer.Option(..., "--in", help="The step that carried it out: specify, design, implement, test or code."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Record that a step carried out a finding's proposal ('done in <step>: ...'); the finding stays open for review.

    Implements REQ-CLI-011.
    """
    _write_finding(change, as_json, "done", lambda ch: mark_finding_done(ch, finding_id, step, text))


# @req REQ-CLI-011
@finding_app.command("close")
def finding_close(
    finding_id: str = typer.Argument(..., metavar="ID", help="The finding's ID, e.g. R1."),
    text: str = typer.Argument(..., help="What review confirmed."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Tick a finding and record what review confirmed ('confirmed in review: ...').

    Implements REQ-CLI-011.
    """
    _write_finding(change, as_json, "close", lambda ch: close_finding(ch, finding_id, text))


# @req REQ-CLI-011
def _write_finding(ref: str, as_json: bool, action: str, write: Callable[[Change], Finding]) -> None:
    """Run one of the finding writers on the change and print the finding as `specworks cycle` reads it, with the path of
    the check artifact it wrote: the one its ID's letter names."""
    ws, mod, ch = require_change(ref, as_json)
    started = time.monotonic()
    try:
        finding = write(ch)
    except FindingError as exc:  # the message names the file: shown relative to the workspace root, as every path
        raise FindingError(_relative_paths(ws, ch, str(exc))) from None
    path = ch.path / check_artifact_for(finding.id).file
    rel = ws.rel(path)
    data = {**change_dict(ws, mod, ch), "finding": {**finding.to_dict(), "done": finding.done}, "path": rel}
    record(ws, mod, ch, "finding", started, action=action, id=finding.id, type=finding.type, step=finding.phase)  # never the finding's text
    emit(data, as_json, f"{finding.id} {finding.type or '?'} -> {finding.phase} ({'done' if finding.done else 'open'})\n{rel}")


def _relative_paths(ws: Workspace, ch: Change, message: str) -> str:
    """``message`` with the path of every check artifact of the change shown relative to the workspace root."""
    for path in sorted((ch.path / a.file for a in check_artifacts()), key=lambda p: -len(str(p))):
        message = message.replace(str(path), ws.rel(path))
    return message


def _rel(ws: Workspace, path: Path) -> str:
    try:
        return ws.rel(path)
    except ValueError:  # a file of the repository outside the workspace
        return path.as_posix()


# @req REQ-CLI-023
@app.command("validate")
def validate_cmd(
    change: str = ChangeOpt,
    base: str | None = typer.Option(None, "--base", help="Branch to diff against (default: origin's default branch)."),
    no_run: bool = typer.Option(False, "--no-run", help="Do not run test/lint/typecheck (reported as warnings)."),
    write: bool = typer.Option(False, "--write", help="Write validation.md: a finding per failed blocking check, and the verdict in its Summary."),
    fresh: bool = FreshOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Final check before close (validate phase): completeness, correctness, coherence (exit 1 on FAIL); read-only unless --write."""
    ws, mod, ch = require_change(change, as_json)
    started = time.monotonic()
    ctx = GateContext(ws, mod, ch, run_tests=not no_run, base=base, reuse_runs=not fresh)
    written: str | None = None
    if write:  # REQ-CLI-023: validation.md kept in step with the checks; the verdict is the one after the write
        try:
            checks, path = write_validation(ctx)
        except FindingError as exc:
            fail(_relative_paths(ws, ch, str(exc)), as_json)
        written = ws.rel(path)
    else:
        checks = validate_change(ctx)
    result = summary(checks)
    record(ws, mod, ch, "validate", started, verdict=result["verdict"], critical=result["critical"], warnings=result["warnings"])
    data = {**change_dict(ws, mod, ch), **result, "checks": [c.to_dict() for c in checks], **({"path": written} if written else {})}
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
    if written:
        lines.append(written)
    emit(data, as_json, "\n".join(lines))
    if result["verdict"] != "PASS":
        raise typer.Exit(1)


# @req REQ-CLI-007
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
    started = time.monotonic()
    ref = mod.qualify(ch.name)
    # The architecture is checked first: a missing file fails fast, before the project's commands run.
    missing = [] if mod.architecture_path.is_file() else [ws.rel(mod.architecture_path)]
    if missing and not dry_run:
        fail(f"{ref} has no {missing[0]}: write the module's architecture before close (/specworks-close)", as_json)
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
    data = {**change_dict(ws, mod, ch), "dryRun": dry_run, "merges": [m.to_dict(ws) for m in merges], "missing": missing, "archivedTo": None}
    lines = [f"{'would merge' if dry_run else 'merged'} {m.cap.ref} -> {ws.rel(m.spec_path)}{' (new)' if m.created else ''}: {m.summary()}" for m in merges]
    lines = lines or ["no delta specs to merge (skip_specs)"]
    lines += [f"missing: {path} (write it before close)" for path in missing]
    if not dry_run:
        try:
            target = close_change(merges, ch, mod.config.archive_path)
        except OSError as exc:
            fail(str(exc), as_json)
        data["archivedTo"] = ws.rel(target)
        data["phase"] = "done"
        lines.append(f"archived -> {data['archivedTo']}")
        ch.path = target  # the event goes into the archived folder; the commit that follows sends it
        record(ws, mod, ch, "close", started, merged=len(merges))
    emit(data, as_json, "\n".join(lines))


@app.command()
def run(
    key: str = typer.Argument(..., help="Command to run: test, lint, typecheck, build or format."),
    change: str | None = typer.Option(None, "--change", "-c", help="Run in the module owning this change."),
    as_json: bool = JsonOpt,
) -> None:
    """Run one of the project's configured commands in the right module folder (exit code passes through)."""
    ch = None
    if change:
        ws, mod, ch = require_change(change, as_json)
    else:
        ws = workspace(as_json)
        mod = ws.current
    started = time.monotonic()
    result = cached_run(ws, mod, key, reuse=False, capture=as_json)
    if ch is not None:
        record(ws, mod, ch, "run", started, key=key, exitCode=result.exit_code)
    if as_json:
        typer.echo(
            json.dumps(
                {"key": key, "command": result.command, "cwd": result.cwd, "exitCode": result.exit_code, "ok": result.ok, "tail": result.tail()},
                indent=2,
            )
        )
    raise typer.Exit(result.exit_code)
