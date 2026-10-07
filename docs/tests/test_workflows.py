"""Structural checks for the documentation workflows."""

from __future__ import annotations

from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _job(text: str, name: str) -> str:
    """Return the YAML block of one job, up to the next top-level job."""
    start = text.index(f"\n  {name}:\n")
    rest = text[start + 1 :]
    end = next(
        (
            i
            for i, line in enumerate(rest.splitlines(keepends=True))
            if i > 0 and line.startswith("  ") and not line.startswith("   ") and line.strip()
        ),
        None,
    )
    lines = rest.splitlines(keepends=True)
    return "".join(lines[:end] if end is not None else lines)


def test_docs_workflow_builds_on_pull_requests_and_main() -> None:
    text = (WORKFLOWS / "docs.yml").read_text(encoding="utf-8")

    assert "pull_request:" in text
    assert "push:" in text and "- main" in text
    assert 'python-version: "3.12"' in text
    assert 'pip install -e ".[docs]"' in text
    assert "pytest docs/tests" in text
    assert "python -m sphinx -W --keep-going -b html docs docs/_build/html" in text


def test_docs_workflow_deploys_only_from_main_with_scoped_permissions() -> None:
    text = (WORKFLOWS / "docs.yml").read_text(encoding="utf-8")
    build = _job(text, "build")
    deploy = _job(text, "deploy")

    # The workflow default is read-only; only the deploy job may write Pages.
    top = text[: text.index("\njobs:")]
    assert "contents: read" in top
    assert "pages: write" not in top and "pages: write" not in build
    assert "pages: write" in deploy and "id-token: write" in deploy

    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in deploy
    assert "actions/upload-pages-artifact@v5" in build
    assert "actions/configure-pages@v6" in deploy
    assert "actions/deploy-pages@v5" in deploy
    assert "name: github-pages" in deploy
    assert "steps.deployment.outputs.page_url" in deploy


def test_link_check_runs_on_schedule_and_demand_only() -> None:
    text = (WORKFLOWS / "docs-links.yml").read_text(encoding="utf-8")
    triggers = text[: text.index("\njobs:")]

    assert "schedule:" in triggers
    assert "workflow_dispatch:" in triggers
    assert "pull_request" not in triggers
    assert "push:" not in triggers
    assert "contents: read" in text
    assert "-b linkcheck" in text
