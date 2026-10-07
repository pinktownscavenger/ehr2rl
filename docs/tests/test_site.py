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
