"""Sphinx configuration for the ehr2rl documentation site."""

from __future__ import annotations

import ehr2rl

project = "ehr2rl"
author = "ehr2rl contributors"
copyright = "ehr2rl contributors"
release = ehr2rl.__version__
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

source_suffix = {".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "tests"]

# Treat every unresolved cross-reference as a warning; the build runs with -W.
nitpicky = True

# Each entry must be one fully qualified type from an optional dependency
# (d3rlpy, google-cloud-bigquery) that cannot resolve without that package.
# Never add regex ignores or ehr2rl.* names: those would hide real breakage.
nitpick_ignore: list[tuple[str, str]] = []

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}

autodoc_member_order = "bysource"
napoleon_google_docstring = False
napoleon_numpy_docstring = True

html_theme = "furo"
html_title = f"ehr2rl {release}"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
