"""Build the documentation site strictly and inspect the generated HTML."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

DOCS_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def built_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return an isolated HTML build of the site, failing on any Sphinx warning."""
    output = tmp_path_factory.mktemp("html")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-W",
            "--keep-going",
            "-b",
            "html",
            str(DOCS_DIR),
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"Strict Sphinx build failed:\n{result.stderr}", pytrace=False)
    return output


def test_strict_build_creates_index(built_site: Path) -> None:
    assert (built_site / "index.html").is_file()


def test_landing_page_has_equal_audience_paths(built_site: Path) -> None:
    html = (built_site / "index.html").read_text(encoding="utf-8")
    for text in (
        "Researchers",
        "Contributors",
        "Synthetic quickstart",
        "API reference",
        "search",
        "research infrastructure",
        "not clinical decision support",
    ):
        assert text in html, f"landing page is missing {text!r}"


def test_landing_css_has_accessibility_states() -> None:
    css = (DOCS_DIR / "_static" / "custom.css").read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "max-width: 320px" in css
    assert "@import" not in css
