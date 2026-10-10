# Documentation workflow

The site is built with [Sphinx](https://www.sphinx-doc.org/), pages are written
in Markdown with [MyST](https://myst-parser.readthedocs.io/), and the theme is
[Furo](https://pradyunsg.me/furo/). Sources live in `docs/`.

## Build locally

With the `docs` extra installed in a Python 3.12 environment:

```bash
.venv-docs/bin/python -m sphinx -W --keep-going -b html docs docs/_build/html
.venv-docs/bin/python -m http.server 8000 --directory docs/_build/html
```

Then open `http://localhost:8000`. `docs/_build/` is ignored by Git; never
commit built HTML.

Type names link to the Python, NumPy, and pandas docs through object
inventories committed in `docs/_intersphinx/`, so the build works offline.
Refresh them occasionally, for example before a release. This downloads every
inventory listed in `intersphinx_mapping`:

```bash
.venv-docs/bin/python -c "import runpy; [print(u + '/objects.inv', 'docs/' + f) for u, (f, _) in runpy.run_path('docs/conf.py')['intersphinx_mapping'].values()]" | while read -r url out; do curl -sSfL -o "$out" "$url"; done
```

It uses `curl` because numpy.org rejects Python's default HTTP client.

Rebuild strictly afterwards and commit the updated files.

## Warnings are errors

The build runs with `-W` and `nitpicky = True`, so any warning fails it:

- a page that is not in a table of contents;
- a broken internal link or cross-reference;
- an API object that cannot be imported;
- a type in a signature that cannot be resolved.

Do not silence warnings. The only exception is `nitpick_ignore` in
`docs/conf.py`, which may list individual fully qualified types from optional
dependencies that cannot resolve without them, each with a comment. Regex
ignores and `ehr2rl` names are not allowed, and a test enforces this.

## Writing pages

| Section | Directory | For |
|---|---|---|
| Get started, Use ehr2rl | `docs/use/` | Task-oriented guides |
| Understand | `docs/concepts/` | How things work and why |
| Develop | `docs/develop/` | Contributors |
| Reference | `docs/api/` | Generated API pages |

New pages must be added to a `toctree` in `docs/index.md` or `docs/api/index.md`.
Link to API objects with roles such as `` {py:class}`~ehr2rl.EHRDataset` `` so a
renamed object fails the build instead of leaving a dead link.

## Tested examples

Examples users are expected to run should come from a file that tests execute.
The synthetic quickstart includes `examples/docs_quickstart.py` with
`literalinclude`, and `tests/test_examples.py` runs that file, so the page
cannot drift from the library.

Examples that need credentials or optional extras cannot run in CI. Check them
by hand before merging, and keep them to bounded cohorts with an explicit
`maximum_bytes_billed`.

## API pages

API pages are curated, not generated recursively. To document a public object:

1. Give it a NumPy-style docstring with `Parameters`, `Returns`, and `Raises`
   sections as needed. Dataclasses list their fields under `Parameters`.
2. Add it to `PUBLIC_API` in `tests/test_public_docs.py`.
3. Add a directive to the right page in `docs/api/`, inside an `{eval-rst}`
   block. Bare MyST autodoc directives render as plain text without a warning.

````markdown
```{eval-rst}
.. autoclass:: ehr2rl.EHRDataset
   :members: copy_with, featurize
```
````

`docs/tests/test_site.py` fails if the rendered objects differ from
`PUBLIC_API` in either direction.

## Site behavior

`docs/_static/site.js` adds three behaviors on top of Furo without changing its
markup:

- **In-place navigation.** Links to other pages swap the article, footer, and
  "On this page" contents instead of reloading, so the left sidebar keeps its
  place. The search and index pages, files under `_static/`, and anything that
  fails to load fall back to a normal page load.
- **Live search.** The sidebar search box shows the top results while typing,
  using Sphinx's own index and ranking (`Search._parseQuery` and
  `Search._performSearch` from `searchtools.js`). Enter still opens the full
  search page. `docs/tests/test_site.py` fails if a Sphinx upgrade removes
  those functions.
- **"On this page" tracking.** Marks the section being read. It replaces
  Furo's tracker, which only follows the first page loaded.

Animations live in `docs/_static/custom.css` and are switched off for readers
who prefer reduced motion. Check behavior changes in a browser at desktop and
phone widths, in light and dark mode: the build cannot test JavaScript.

## Tests and CI

```bash
.venv-docs/bin/python -m pytest docs/tests
```

The documentation workflow builds the site strictly and runs these tests on
every pull request and every push to `main`. Merges to `main` deploy the site
to GitHub Pages. A separate workflow checks external links weekly; broken links
there do not block pull requests. See [Releases](releases.md).
