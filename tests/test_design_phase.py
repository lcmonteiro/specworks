"""Design phase: the design gate (API recorded in design.md, stubs exist, build and tests still pass)."""

import pytest

from helpers import REF, run_json
from support.design_phase import make_planned


@pytest.fixture
def planned(project):
    return make_planned(project)


def test_phase_order_has_interface_between_propose_and_implement(planned):
    code, data = run_json("phase", "design", "--change", REF)
    assert code == 0 and data["phase"] == "design"
    code, data = run_json("status", "--change", REF)
    assert data["phase"] == "design" and data["phases"].index("specify") < data["phases"].index("design") < data["phases"].index("implement")
