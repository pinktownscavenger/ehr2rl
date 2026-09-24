# ehr2rl

![PyPI](https://img.shields.io/pypi/v/ehr2rl)
![CI](https://github.com/pinktownscavenger/ehr2rl/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/pypi/pyversions/ehr2rl)

`ehr2rl` is a Python library for turning MIMIC-IV-style electronic health record
data into datasets ready for offline reinforcement learning research.

Healthcare ML libraries are usually built for supervised prediction, while
offline RL libraries expect a clean state-action-reward dataset that already
exists. `ehr2rl` fills the gap between those worlds: loading longitudinal EHR
tables, representing patient trajectories, shaping rewards, estimating observed
behavior, and exporting data for tools such as `d3rlpy`.

[PyPI](https://pypi.org/project/ehr2rl) ·
[GitHub](https://github.com/pinktownscavenger/ehr2rl)

## Features

- Load and align MIMIC-IV admissions, vitals, and lab tables into patient trajectories.
- Build bounded MIMIC-IV v3.1 cohorts through BigQuery with dry-run billing guards.
- Resolve validated v3.1 itemid maps through named feature presets.
- Construct fluids and vasopressor actions from ICU medication events.
- Construct reward signals, including mortality and SOFA delta, with a
  swappable reward interface, plus readmission and weighted composite rewards.
- Estimate observed clinician behavior policy from historical data.
- Export training-ready datasets for offline RL with `d3rlpy`, including
  optional provenance sidecars.
- Generate synthetic MIMIC-IV-style data for development and testing without
  credentialed access.

## Installation

`ehr2rl` targets Python 3.10+.

Minimal install:

```bash
pip install ehr2rl
```

For `d3rlpy` export:

```bash
pip install "ehr2rl[d3rlpy]"
```

For credentialed MIMIC-IV BigQuery pipelines and smoke tests:

```bash
pip install "ehr2rl[bigquery]"
```

For the full BigQuery-to-`d3rlpy` example:

```bash
pip install "ehr2rl[all]"
```

## Quickstart

Start with synthetic data:

```python
from ehr2rl import make_synthetic_dataset, MortalityReward

ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)
ds = MortalityReward().shape(ds)

print(f"Loaded {len(ds)} patient trajectories")
print(f"State shape: {ds.trajectories[0].states.shape}")
```

Full synthetic-to-`d3rlpy` round trip:

```python
from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset, to_d3rlpy

ds = make_synthetic_dataset(
    n_patients=25,
    trajectory_length=24,
    seed=7,
    include_medication_metadata=True,
)

policy = BehaviorPolicy().fit(ds)
ds = MortalityReward().shape(ds, policy=policy)

# Requires: pip install ehr2rl[d3rlpy]
mdp_dataset = to_d3rlpy(ds)
```

The synthetic path is the default development path so tests and examples do not
require access to MIMIC-IV.

## BigQuery MIMIC-IV v3.1 Pipeline

v0.2 makes BigQuery the primary real-data path for MIMIC-IV v3.1. The local CSV
loader remains available for backward compatibility and offline work, but it is
frozen at its existing demo-schema behavior and does not receive new v3.1
validation, itemid maps, feature presets, or medication action construction.

Every BigQuery query goes through a dry-run estimate before execution and sets
`maximum_bytes_billed` on the real job as a server-side backstop.

```python
from google.cloud import bigquery

from ehr2rl.actions import ActionConfig, DoseBins
from ehr2rl.bigquery import (
    BigQueryCohort,
    CohortCriteria,
    GuardedBigQueryClient,
    load_mimiciv_bigquery_dataset,
)
from ehr2rl.data.itemid_maps import load_itemid_map
from ehr2rl.data.presets import get_feature_preset

client = GuardedBigQueryClient(
    bigquery.Client(project="YOUR_BILLING_PROJECT_ID"),
    maximum_bytes_billed=25_000_000_000,
    cache_dir=".ehr2rl_cache",
    query_timeout=60,
)

ds = load_mimiciv_bigquery_dataset(
    client=client,
    cohort=BigQueryCohort(CohortCriteria(cohort_size=25)),
    preset=get_feature_preset("vitals_only"),
    itemid_map=load_itemid_map("v3_1"),
    action_config=ActionConfig(
        vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3, 0.6)),
        fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0, 1000.0)),
    ),
)
```

Feature presets reference canonical clinical names rather than raw itemids:

```python
from ehr2rl.data.itemid_maps import load_itemid_map
from ehr2rl.data.presets import get_feature_preset

resolved = get_feature_preset("sepsis3_core").resolve(load_itemid_map("v3_1"))
print(sorted(resolved))
```

Medication actions are represented as two columns: vasopressor bin and fluid
bin. Synthetic datasets can opt into that shape for tests and examples:

```python
from ehr2rl import make_synthetic_dataset

ds = make_synthetic_dataset(include_medication_metadata=True)
print(ds[0].metadata["action_names"])
```

Exported real datasets can write a JSON provenance sidecar:

```python
from ehr2rl import to_d3rlpy

mdp_dataset = to_d3rlpy(ds, provenance_path="dataset.provenance.json")
```

## Development Install

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy ehr2rl
```

To exercise the optional BigQuery and `d3rlpy` paths in development:

```bash
pip install -e ".[dev,all]"
pytest
```

## MIMIC-IV Access

`ehr2rl` does not ship, mirror, or provide access to MIMIC-IV. Researchers must
obtain any clinical data through the appropriate credentialed channels, such as
PhysioNet, and comply with the applicable data use agreements.

Credentialed users can run a bounded BigQuery smoke test without downloading the
dataset. The test is opt-in, applies a per-query bytes-billed cap, and disables
BigQuery retries so credential or network failures return quickly.

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_BILLING_PROJECT_ID
EHR2RL_RUN_BIGQUERY_SMOKE=1 \
EHR2RL_BIGQUERY_BILLING_PROJECT=YOUR_BILLING_PROJECT_ID \
EHR2RL_BIGQUERY_TIMEOUT_SECONDS=60 \
pytest tests/test_bigquery_smoke.py
```

The smoke helper uses the MIMIC-IV v3.1 BigQuery datasets exposed as
`physionet-data.mimiciv_3_1_hosp` and `physionet-data.mimiciv_3_1_icu`.

## Known Limitations

The local CSV loader is retained for backward compatibility and offline/no-GCP
development, but v0.2 real-data validation is BigQuery-first.

`d3rlpy` currently prints a Gym deprecation warning under NumPy 2.x; this is an
upstream issue and does not affect functionality.

## Clinical Disclaimer

`ehr2rl` is research infrastructure. It is not clinical decision support, does
not validate treatment recommendations, and does not define a clinically
authoritative reward function. Reward design and interpretation remain the
responsibility of the researcher.

## Roadmap

Future priorities:

- Minari export.
- Standalone pre-flight validation.
- CLI tooling and a documentation site.
- Additional dataset families such as eICU, MIMIC-III, and OMOP-CDM.

## Contributing

Issues and pull requests are welcome. For v0.2, the most useful contributions
are BigQuery schema checks, validated itemid-map updates, synthetic-data edge
cases, documentation fixes, and export compatibility improvements.

If you have access to full MIMIC-IV v3.1 and spot a schema mismatch, opening an
issue with the table name and column is especially helpful.

## Citation

```bibtex
@software{ehr2rl2026,
  author  = {Bilal Malik},
  title   = {ehr2rl: Bridging MIMIC-IV and Offline Reinforcement Learning},
  year    = {2026},
  version = {0.2.0},
  url     = {https://github.com/pinktownscavenger/ehr2rl}
}
```
