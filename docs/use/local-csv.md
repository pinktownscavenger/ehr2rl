# Local CSV loading (compatibility)

:::{warning}
This path is kept for offline and backward-compatible workflows. It is
**frozen** at its v0.1 demo-schema behavior and does not receive itemid maps,
feature presets, label validation, or medication actions. For MIMIC-IV v3.1,
use the [BigQuery workflow](bigquery.md) instead.
:::

## What it does

`EHRDataset` can read MIMIC-IV-style CSV tables from a local directory and
build trajectories from them:

```python
from ehr2rl import EHRDataset

ds = (
    EHRDataset("path/to/mimic-iv")
    .load_admissions()
    .load_vitals()
    .load_labs()
    .featurize()
)
```

Each loader looks for the standard MIMIC-IV file first and then a flat fallback
name in the same directory:

| Method | Default file | Fallback | Required columns |
|---|---|---|---|
| `load_admissions()` | `hosp/admissions.csv.gz` | `admissions.csv` | `subject_id`, `hadm_id`, `admittime`, `dischtime`, `hospital_expire_flag` |
| `load_vitals()` | `icu/chartevents.csv.gz` | `vitals.csv` | `subject_id`, `hadm_id`, `charttime`, `itemid`, `valuenum` |
| `load_labs()` | `hosp/labevents.csv.gz` | `labs.csv` | `subject_id`, `hadm_id`, `charttime`, `itemid`, `valuenum` |

A missing file or column raises `EHRValidationError`.

## Behavior to be aware of

- **Features are raw itemids.** Columns are named `vital_<itemid>` and
  `lab_<itemid>`, not canonical concepts, and no units are converted.
- **Only vitals are resampled.** `load_vitals(resample="1h")` averages vitals
  into hourly bins. Labs keep their original chart times, so a trajectory's
  timesteps are the union of hourly vital bins and lab times.
- **Gaps are forward-filled, then zero-filled.** Before a feature's first
  measurement its value is `0.0`, which is not clinically meaningful.
- **Actions are placeholders.** Every trajectory gets a single all-zero action
  column. Build real actions yourself before training.
- **Mortality comes from `hospital_expire_flag`** and is stored as
  `metadata["died"]` for `MortalityReward`.
- `load_labs(codes=[...])` keeps only the listed lab itemids.

## Smoke loader

`ehr2rl.data.load_mimiciv_smoke_dataset` is a legacy helper that pulls a small
cohort, with a fixed set of vitals and labs, from BigQuery into this same
CSV-era representation. It exists to check credentialed access quickly and is
not intended for research cohorts.

```python
from ehr2rl.data import load_mimiciv_smoke_dataset

ds = load_mimiciv_smoke_dataset(
    billing_project="YOUR_BILLING_PROJECT_ID",
    cohort_size=25,
    maximum_bytes_billed=25_000_000_000,
)
```

It requires `pip install "ehr2rl[bigquery]"` and applies `maximum_bytes_billed`
to every query it runs.
