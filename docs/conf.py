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
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3
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
# Furo's default dark style ("native") underlines module names in code, which
# reads as a link.
pygments_dark_style = "github-dark"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# One muted clinical-green accent. Both values meet WCAG AA (>= 4.5:1) against
# Furo's page and secondary backgrounds in their appearance.
_system_fonts = (
    "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, "
    "sans-serif"
)
_mono_fonts = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#2b6a52",
        "color-brand-content": "#2b6a52",
        "color-brand-visited": "#2b6a52",
        "font-stack": _system_fonts,
        "font-stack--monospace": _mono_fonts,
    },
    "dark_css_variables": {
        "color-brand-primary": "#7cc5a5",
        "color-brand-content": "#7cc5a5",
        "color-brand-visited": "#7cc5a5",
    },
    "source_repository": "https://github.com/pinktownscavenger/ehr2rl/",
    "source_branch": "main",
    "source_directory": "docs/",
}
