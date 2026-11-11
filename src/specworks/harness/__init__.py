"""The harness: the specworks flow as a chatinho chat, one Deep Agent peer per packaged skill.

Needs the ``harness`` extra (chatinho and deepagents, Python 3.12+); only the ``harness`` command imports it.
"""

from __future__ import annotations

from specworks.harness.model import ModelSettingsError, model_from_env
from specworks.harness.session import build_harness, run_harness

__all__ = ["ModelSettingsError", "build_harness", "model_from_env", "run_harness"]
