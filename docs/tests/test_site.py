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
        "research infrastructure",
        "not clinical decision support",
    ):
        assert text in html, f"landing page is missing {text!r}"

    # Global search: Furo's search form, plus the index it queries.
    assert 'role="search"' in html and 'action="search.html"' in html
    assert 'name="q"' in html
    assert (built_site / "searchindex.js").is_file()


def test_landing_css_has_accessibility_states() -> None:
    css = (DOCS_DIR / "_static" / "custom.css").read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "max-width: 320px" in css
    assert "@import" not in css


def _public_api_spec():
    """Load the approved API list from the package tests, the single source."""
    import importlib.util

    path = DOCS_DIR.parent / "tests" / "test_public_docs.py"
    spec = importlib.util.spec_from_file_location("test_public_docs", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _object_ids(html_path: Path) -> set[str]:
    import re

    return set(re.findall(r'<dt class="sig[^"]*" id="(ehr2rl[^"]+)"', html_path.read_text("utf-8")))


def test_curated_api_surface(built_site: Path) -> None:
    spec = _public_api_spec()
    class_paths = {name: f"{module}.{name}" for module, name in spec.PUBLIC_API}
    expected = set(class_paths.values())
    expected |= {
        f"{class_paths[cls]}.{member}"
        for cls, members in spec.PUBLIC_MEMBERS.items()
        for member in members
    }
    # The legacy smoke loader is documented only on the compatibility page.
    expected.discard("ehr2rl.data.load_mimiciv_smoke_dataset")

    rendered: set[str] = set()
    for page in (built_site / "api").glob("*.html"):
        rendered |= _object_ids(page)

    assert rendered == expected
    assert _object_ids(built_site / "use" / "local-csv.html") == {
        "ehr2rl.data.load_mimiciv_smoke_dataset"
    }

    api_text = "".join(p.read_text("utf-8") for p in (built_site / "api").glob("*.html"))
    for private in (
        "_stack",
        "_cohort_cte",
        "_validate_shapes",
        "_validate_live_item_labels",
        "fluid_amount",
        "arrays_for_d3rlpy",
        "provenance_from_mapping",
    ):
        assert private not in api_text, f"{private} leaked into the API reference"


def test_nitpick_ignore_is_narrow() -> None:
    import runpy

    conf = runpy.run_path(str(DOCS_DIR / "conf.py"))
    assert not conf.get("nitpick_ignore_regex")
    for entry in conf["nitpick_ignore"]:
        role, target = entry
        assert role.startswith("py:")
        assert not target.startswith("ehr2rl"), f"{target} hides a broken ehr2rl reference"
        assert "*" not in target and "." in target, f"{target} is not one qualified type"


def test_concept_pages_cover_invariants_and_limitations(built_site: Path) -> None:
    import html
    import re

    concept_dir = built_site / "concepts"
    assert concept_dir.is_dir(), "concept pages were not built"
    text = " ".join(
        html.unescape(re.sub(r"<[^>]+>", " ", page.read_text("utf-8")))
        for page in concept_dir.glob("*.html")
    )
    text = re.sub(r"\s+", " ", text)
    for phrase in (
        "(T, D)",
        "(T, A)",
        "maximum_bytes_billed",
        "itemid map",
        "research infrastructure",
        "not clinical decision support",
    ):
        assert phrase in text, f"concept pages are missing {phrase!r}"


def test_contributor_path_and_readme_link(built_site: Path) -> None:
    import html
    import re

    develop_dir = built_site / "develop"
    assert develop_dir.is_dir(), "contributor pages were not built"
    text = " ".join(
        html.unescape(re.sub(r"<[^>]+>", " ", page.read_text("utf-8")))
        for page in develop_dir.glob("*.html")
    )
    text = re.sub(r"\s+", " ", text)
    for phrase in (
        "pytest",
        "ruff check .",
        "mypy ehr2rl",
        "Adding a reward",
        "Adding features and itemids",
        "Documentation workflow",
    ):
        assert phrase in text, f"contributor pages are missing {phrase!r}"

    readme = (DOCS_DIR.parent / "README.md").read_text(encoding="utf-8")
    assert "https://pinktownscavenger.github.io/ehr2rl/" in readme


def test_build_does_not_need_network(tmp_path: Path) -> None:
    """A network outage must not fail the strict build (and so block PRs)."""
    import os

    unreachable = "http://127.0.0.1:9"
    env = {**os.environ, "HTTP_PROXY": unreachable, "HTTPS_PROXY": unreachable}
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-W", "--keep-going", "-b", "html", "-E",
         str(DOCS_DIR), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr[-2000:]


def test_site_script_loads_deferred_on_every_page(built_site: Path) -> None:
    import re

    pages = [p for p in built_site.rglob("*.html") if "_static" not in p.parts]
    assert pages
    for page in pages:
        html = page.read_text("utf-8")
        tags = [t for t in re.findall(r"<script[^>]*>", html) if "_static/site.js" in t]
        assert len(tags) == 1 and "defer" in tags[0], (
            f"{page.relative_to(built_site)} does not load site.js deferred"
        )


def test_live_search_relies_only_on_existing_sphinx_search_api(built_site: Path) -> None:
    """site.js calls these searchtools.js members; fail loudly if Sphinx renames them."""
    searchtools = (built_site / "_static" / "searchtools.js").read_text("utf-8")
    for member in ("_parseQuery:", "_performSearch:", "setIndex:", "hasIndex:"):
        assert member in searchtools, f"searchtools.js no longer defines {member}"
    for asset in ("searchindex.js", "_static/language_data.js"):
        assert (built_site / asset).is_file()


def test_target_headings_are_not_highlighted(built_site: Path) -> None:
    html = (built_site / "index.html").read_text("utf-8")
    assert html.count("--color-highlight-on-target: transparent") >= 2  # light and dark


def test_motion_respects_reduced_motion_preference() -> None:
    css = (DOCS_DIR / "_static" / "custom.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "@keyframes" in css
