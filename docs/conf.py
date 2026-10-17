"""Sphinx configuration for the specworks documentation.

Build it with:

    uv run --group docs sphinx-build -W --keep-going docs docs/_build/html
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from specworks import __version__  # noqa: E402

project = "specworks"
author = "specworks contributors"
copyright = "specworks contributors"
version = release = __version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
# example/ is the project the tutorial builds: its files are shown with literalinclude, not built as pages.
exclude_patterns = ["_build", "example/**", "diagrams/**", "README.md"]

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist", "attrs_inline"]
myst_heading_anchors = 4

autodoc_member_order = "bysource"
autodoc_inherit_docstrings = False
autodoc_typehints = "description"
autodoc_default_options = {"members": True, "show-inheritance": True}

html_theme = "furo"
html_title = f"specworks {release}"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

copybutton_prompt_text = "$ "
copybutton_only_copy_prompt_lines = False

mermaid_version = "11.4.1"
