# Development setup

## Install

Clone the repository and install it in editable mode with the development
tools. The package supports Python 3.10 and later.

```bash
git clone https://github.com/pinktownscavenger/ehr2rl.git
cd ehr2rl
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Add extras to work on the optional paths:

| Install | Adds |
|---|---|
| `pip install -e ".[dev]"` | `pytest`, `pytest-cov`, Ruff, Black, mypy |
| `pip install -e ".[dev,all]"` | The above plus `d3rlpy` and the BigQuery client, so their tests run instead of being skipped |
| `pip install -e ".[docs]"` | Sphinx and the site toolchain; needs Python 3.12 or later |

The documentation toolchain needs a newer Python than the package. A separate
environment for it is simplest:

```bash
python3.12 -m venv .venv-docs
.venv-docs/bin/pip install -e ".[docs]"
```

## Quality checks

CI runs these three commands on Python 3.10 and 3.11 for every push and pull
request. Run them before you push:

```bash
pytest
ruff check .
mypy ehr2rl
```

Ruff uses a line length of 88 and targets Python 3.10. mypy checks the
`ehr2rl` package only.

## Credentialed smoke test

`tests/test_bigquery_smoke.py` runs a real 25-patient load against MIMIC-IV on
BigQuery. It is skipped unless you opt in, and it never runs in CI. You need
credentialed MIMIC-IV access and a billing project; see
[MIMIC-IV through BigQuery](../use/bigquery.md#prerequisites).

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_BILLING_PROJECT_ID
EHR2RL_RUN_BIGQUERY_SMOKE=1 \
EHR2RL_BIGQUERY_BILLING_PROJECT=YOUR_BILLING_PROJECT_ID \
EHR2RL_BIGQUERY_TIMEOUT_SECONDS=60 \
pytest tests/test_bigquery_smoke.py
```

Always set `EHR2RL_BIGQUERY_BILLING_PROJECT` to your own project. The test caps
every query at 25 GB billed and disables retries, so credential and network
failures surface quickly.

## Troubleshooting

**`ModuleNotFoundError: No module named 'ehr2rl'` after an editable install on
macOS.** Python 3.12 and later skip `.pth` files that carry the macOS "hidden"
file flag, which some sync and backup tools set. Clear it:

```bash
chflags nohidden .venv/lib/python3*/site-packages/*.pth
```
