"""Helpers shared by the findings tests of several capabilities."""

from helpers import REF
from specworks.cli.output import resolve_change
from specworks.core.workspace import load_workspace
from specworks.workflow.artifacts import CheckArtifact

REVIEW = f".specworks/changes/active/{REF}/review.md"
# review.md as a check artifact, as the schema declares it (REQ-FLOW-018)
REVIEW_ARTIFACT = CheckArtifact(id="review", file="review.md", letter="R", phase="review", blocks=("review", "validate"))
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
