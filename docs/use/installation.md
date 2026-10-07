# Installation

`ehr2rl` supports Python 3.10 and later. The base install is enough for
synthetic data, rewards, and behavior-policy estimation. Real-data and export
features live behind optional extras so that a plain install stays small.

## Base install

```bash
pip install ehr2rl
```

This installs NumPy, pandas, scikit-learn, and SciPy. It is all you need for the
[synthetic quickstart](synthetic-quickstart.md).

## Optional extras

| Extra | Install | Adds | Needed for |
|---|---|---|---|
| `d3rlpy` | `pip install "ehr2rl[d3rlpy]"` | `d3rlpy` | `to_d3rlpy` export |
| `bigquery` | `pip install "ehr2rl[bigquery]"` | `google-cloud-bigquery`, `google-cloud-bigquery-storage`, `db-dtypes`, `pyarrow` | MIMIC-IV v3.1 through BigQuery |
| `all` | `pip install "ehr2rl[all]"` | Both of the above | The full BigQuery-to-`d3rlpy` workflow |

Quote the argument (`"ehr2rl[d3rlpy]"`) so shells such as zsh do not treat the
square brackets as a glob pattern.

Importing `ehr2rl` never requires an extra. Optional packages are imported only
when you call a function that needs them, and that function raises an
`ImportError` naming the extra to install.

## Contributor installs

From a clone of the repository:

| Extra | Install | Use |
|---|---|---|
| `dev` | `pip install -e ".[dev]"` | Tests, Ruff, and mypy |
| `dev,all` | `pip install -e ".[dev,all]"` | Tests that exercise the BigQuery and `d3rlpy` paths |
| `docs` | `pip install -e ".[docs]"` | Building this documentation site (Python 3.12 or later) |

## Data access

`ehr2rl` does not ship, mirror, or provide access to MIMIC-IV. To work with real
data you need credentialed access through
[PhysioNet](https://physionet.org/content/mimiciv/) and must follow its data use
agreement. Everything else in these guides works without it.
