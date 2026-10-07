# Releases and deployment

Package releases and documentation deployments are independent. Publishing a
release does not deploy the docs, and deploying the docs does not publish a
release.

## Package releases

Packages are published to PyPI by the `Publish` workflow
(`.github/workflows/publish.yml`) using trusted publishing; no API token is
stored in the repository.

1. Update the version in **both** `pyproject.toml` and `ehr2rl/__init__.py`.
2. Move the `Unreleased` entries in `CHANGELOG.md` under the new version and
   date.
3. Merge to `main` with CI green.
4. Optionally rehearse on TestPyPI: run the `Publish` workflow manually with
   `testpypi`.
5. Tag the release commit and push the tag:

   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

A tag matching `v*.*.*` runs the tests, builds the sdist and wheel, checks them
with `twine check`, and publishes to PyPI. The workflow can also publish to
PyPI from a manual run.

## Documentation deployment

The `Docs` workflow (`.github/workflows/docs.yml`) runs on every pull request
and every push:

- **Pull requests and branches** build the site strictly and run the
  documentation tests. Nothing is deployed, and the job has read-only
  permissions.
- **Pushes to `main`** also upload the built site and deploy it to GitHub Pages
  at <https://pinktownscavenger.github.io/ehr2rl/>.

The site always shows the latest `main`. There is no per-version documentation
yet, so the docs can briefly describe unreleased behavior between a merge and
the next release.

## Link checking

The `Docs links` workflow (`.github/workflows/docs-links.yml`) runs Sphinx's
link checker every week and on demand. It never runs on pull requests, so a
temporarily unreachable external site cannot block a contribution. Check its
results in the Actions tab and fix or replace broken links.
