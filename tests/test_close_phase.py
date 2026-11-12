"""
Close phase: capability registration, delta merge into living specs, requirements index, archive.
"""

from specworks.specs.specfile import parse_spec


def test_a_heading_inside_a_delta_requirement_is_reported():
    doc = parse_spec("## ADDED Requirements\n\n### Requirement: REQ-AUTH-003 C\nThe system SHALL c.\n\n### Details\nMore.\n")
    assert [line for line, _ in doc.problems] == [6] and "### Details" in doc.problems[0][1]
    assert "More." not in doc.requirements[0].description
