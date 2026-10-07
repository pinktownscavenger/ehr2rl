# MIMIC-IV through BigQuery

BigQuery is the recommended way to build datasets from MIMIC-IV v3.1. Queries
run against PhysioNet's hosted copy, so you never download the database. Every
query is bounded, estimated with a dry run first, and capped in bytes billed.

:::{important}
Real queries cost money and need credentialed access. Start with a small cohort
and a cache directory, and read [Costs and limits](#costs-and-limits) before
raising either.
:::

## Prerequisites

1. **Credentialed MIMIC-IV access** on [PhysioNet](https://physionet.org/content/mimiciv/),
   with the data use agreement signed.
2. **BigQuery access to `physionet-data`.** Link a Google account to your
   PhysioNet profile and request cloud access from the MIMIC-IV project page.
3. **A Google Cloud billing project.** Queries are billed to it.
4. **The BigQuery extra:** `pip install "ehr2rl[bigquery]"`.

Authenticate with Application Default Credentials:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_BILLING_PROJECT_ID
```

## Load a cohort

```python
from google.cloud import bigquery

from ehr2rl.actions import ActionConfig, DoseBins
from ehr2rl.bigquery import (
    BigQueryCohort,
    CohortCriteria,
    GuardedBigQueryClient,
    load_mimiciv_bigquery_dataset,
)
from ehr2rl.data import get_feature_preset
from ehr2rl.data.itemid_maps import load_itemid_map

client = GuardedBigQueryClient(
    bigquery.Client(project="YOUR_BILLING_PROJECT_ID"),
    maximum_bytes_billed=25_000_000_000,  # 25 GB per query
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

The result is an `EHRDataset` with one trajectory per hospital admission,
canonical features as states, and two-column medication actions. See
[Medication actions](actions.md) for the action settings.

## How guarded queries work

`GuardedBigQueryClient.query_dataframe` runs every query through the same
steps:

1. **Cache check.** The cache key is a SHA-256 hash of the SQL plus extra key
   parts such as the itemid map version and preset name. A cached result
   returns immediately at no cost.
2. **Dry run.** BigQuery estimates the bytes the query would process. If the
   estimate exceeds `maximum_bytes_billed`, `BudgetExceededError` is raised and
   nothing runs.
3. **Capped execution.** The real job is submitted with BigQuery's own
   `maximum_bytes_billed` setting as a server-side backstop.
4. **Cache write.** Results are saved as Parquet in `cache_dir`, or as a pickle
   if `pyarrow` is unavailable.

| Argument | Effect |
|---|---|
| `maximum_bytes_billed` | Per-query cap, checked by dry run and enforced by BigQuery. Required. |
| `cache_dir` | Directory for cached results. Omit it to always query. |
| `query_timeout` | Seconds to wait for each API call and result download. |
| `disable_retries` | Set `True` to turn off the Google client's automatic retries so failures surface immediately. |

BigQuery's own result cache is disabled, so the dry-run estimate always
reflects a real scan.

### Errors

| Exception | When |
|---|---|
| `BudgetExceededError` | The dry run estimates more bytes than the cap. Raised before execution. |
| `BigQueryAuthError` | The dry run or the query fails for **any** reason: credentials, permissions, invalid SQL, timeouts, or network errors. Read the message for the cause. |
| `BigQueryError` | Base class of both. |
| `EHRValidationError` | An itemid's live label differs from the itemid map, or a preset names a concept the map lacks. |

## Costs and limits

- **The cap is per query, not per load.** `load_mimiciv_bigquery_dataset` runs
  up to six queries: two label checks, admissions, vitals, labs, and
  inputevents. Worst-case cost is six times `maximum_bytes_billed`.
- **The cohort is the first N ICU stays, not a random sample.** Stays are
  ordered by `subject_id`, `hadm_id`, and `stay_id` before `LIMIT`, which makes
  results reproducible but not representative.
- **Trajectories are per admission.** If one admission has several ICU stays in
  the cohort, their events merge into one trajectory.
- **Cached queries have no job ID.** Provenance lists only the jobs that
  actually ran in that load.
- Only MIMIC-IV `3_1` is supported.

## Cohort criteria

`CohortCriteria` narrows which ICU stays are eligible before the size limit is
applied:

```python
CohortCriteria(
    cohort_size=25,
    min_age=18,
    max_age=89,
    admission_types=("EW EMER.", "URGENT"),
    min_icu_los_hours=24,
    max_icu_los_hours=240,
)
```

Ages use MIMIC-IV's `anchor_age`. All bounds are inclusive. Stays without an
ICU discharge time are always excluded.

## Features and itemid maps

States use **canonical concepts**, such as `heart_rate` or `lactate`, rather
than raw MIMIC itemids. An itemid map links each concept to versioned itemids,
and a feature preset picks which concepts become state columns.

| Preset | Concepts |
|---|---|
| `vitals_only` | heart rate, respiratory rate, SpO2, temperature (°F and °C) |
| `sepsis3_core` | `vitals_only` plus lactate, creatinine, platelets, WBC |
| `full` | `sepsis3_core` plus hematocrit |

Before loading data, the pipeline checks every itemid in the map against
MIMIC-IV's live `d_items` and `d_labitems` label tables. A missing itemid or a
changed label raises `EHRValidationError`, so the map cannot drift silently.

To inspect what a preset resolves to:

```python
from ehr2rl.data import get_feature_preset
from ehr2rl.data.itemid_maps import load_itemid_map

resolved = get_feature_preset("sepsis3_core").resolve(load_itemid_map("v3_1"))
print({concept: [entry.itemid for entry in entries] for concept, entries in resolved.items()})
```

`load_itemid_map(path=...)` loads your own map in the same JSON format as the
built-in `v3_1` map.

### How states are built

- Columns are concepts, sorted alphabetically; names are in
  `trajectory.metadata["feature_names"]`.
- Each timestep is a distinct chart time for that admission. Measurements are
  **not** resampled to a fixed interval, so steps are irregular.
- Gaps are forward-filled. Before a concept's first measurement its value is
  `0.0`.
- Units are not converted. `temperature_f` and `temperature_c` are separate
  columns, each in its recorded unit.

## Metadata on each trajectory

| Key | Contents |
|---|---|
| `died` | In-hospital death, from `hospital_expire_flag` |
| `feature_names` | State column names |
| `action_names` | `["vasopressor_bin", "fluid_bin"]` |
| `action_sizes` | Number of bins per action column |
| `provenance` | Query hashes, job IDs, map version, preset, timestamp, MIMIC version |

SOFA scores and readmission outcomes are **not** extracted. Add them to
`metadata` yourself before using `SofaReward` or `ReadmissionReward`; see
[Rewards](rewards.md).

## Running in CI

The public test suite and documentation build never submit BigQuery queries or
need credentials. A bounded smoke test is available for credentialed
developers; see the contributor guide.
