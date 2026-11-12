"""
`specworks harness`: the specworks flow as a chatinho chat in the terminal (needs the `harness` extra).
"""

from __future__ import annotations

from specworks.cli.app import app
from specworks.cli.output import workspace
from specworks.core.errors import SpecworksError

#: Why the command cannot run without its extra.
EXTRA_MISSING = "specworks harness needs the harness extra: install specworks[harness]"


# @req REQ-CLI-022
@app.command()
def harness() -> None:
    """
    Open the harness chat, empty: one agent peer per skill, handing work to each other (needs the harness extra).

    A change starts or continues when the user messages a peer, such as ``@refine <request>``.

    Implements REQ-CLI-022.
    """
    # The harness is imported here only, so no other command loads chatinho or deepagents.
    try:
        from specworks.harness import run_harness
    except ImportError:
        raise SpecworksError(EXTRA_MISSING) from None
    ws = workspace(False)
    run_harness(ws)
