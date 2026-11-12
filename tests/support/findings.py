"""Helpers shared by the findings tests of several capabilities."""

from helpers import REF
from specworks.cli.output import resolve_change
from specworks.core.workspace import load_workspace
from specworks.workflow.artifacts import CheckArtifact

REVIEW = f".specworks/changes/active/{REF}/review.md"
# review.md as a check artifact, as the schema declares it (REQ-FLOW-018)
REVIEW_ARTIFACT = CheckArtifact(id="review", file="review.md", letter="R", phase="review", blocks=("review", "validate"))
VALIDATION = f".specworks/changes/active/{REF}/validation.md"
# validation.md as a check artifact, as the schema declares it (REQ-FLOW-018)
VALIDATION_ARTIFACT = CheckArtifact(id="validation", file="validation.md", letter="V", phase="validate", blocks=("validate",))
INSPECTION = f".specworks/changes/active/{REF}/inspection.md"
# inspection.md as a check artifact, as the schema declares it (REQ-FLOW-018)
INSPECTION_ARTIFACT = CheckArtifact(id="inspection", file="inspection.md", letter="I", phase="inspect", blocks=())
TWO_FINDINGS = (
    f"# Review: {REF}\n\n"
    "## Findings\n\n"
    "- [ ] R1 **code-gap** reset ignores case\n"
    "  - **Decision**: back to code: lower-case the email\n"
    "- [x] R2 **tag** missing tag on reset.py\n"
    "  - **Decision**: code fixed\n\n"
    "## Changed files without tags\n\n"
    "- `README.md`: docs\n"
)


def change_of(root):
    ws = load_workspace(root)
    return resolve_change(ws, REF)[1]


def review_path(root):
    return root / REVIEW


def write_review(root, text):
    review_path(root).write_text(text, encoding="utf-8")


def read(root):
    return review_path(root).read_text(encoding="utf-8")


def validation_path(root):
    return root / VALIDATION


def write_validation_md(root, findings, summary=""):
    """validation.md with ``findings`` (lines of Markdown) under ``## Findings`` and ``summary`` under ``## Summary``."""
    validation_path(root).write_text(f"# Validation: {REF}\n\n## Findings\n\n{findings}\n\n## Summary\n\n{summary}", encoding="utf-8")


def read_validation(root):
    return validation_path(root).read_text(encoding="utf-8")


def inspection_path(root):
    return root / INSPECTION


def write_inspection(root, findings):
    """inspection.md with ``findings`` (lines of Markdown) under ``## Findings``."""
    inspection_path(root).write_text(f"# Inspection: {REF}\n\n## Findings\n\n{findings}\n\n## Summary\n\n3 of 5 blocks walked\n", encoding="utf-8")


def read_inspection(root):
    return inspection_path(root).read_text(encoding="utf-8")


def change_files(root):
    """Every file of the change folder and its bytes: what a refused write must leave as it was."""
    folder = root / ".specworks/changes/active" / REF
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}
