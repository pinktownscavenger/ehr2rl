# Pipeline

A dataset can enter `ehr2rl` three ways. All three produce the same
{py:class}`~ehr2rl.EHRDataset`, so everything after loading is shared.

```text
 BigQuery (MIMIC-IV v3.1)      Local CSV (frozen)       Synthetic
          │                           │                     │
          ▼                           ▼                     ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  EHRDataset of PatientTrajectory: states, actions, metadata     │
 └─────────────────────────────────────────────────────────────────┘
          │
          ▼
  Reward function  ──►  rewards filled in, as a new dataset
          │
          ├──►  BehaviorPolicy  ──►  action probabilities, propensities
          │
          ▼
  to_d3rlpy  ──►  MDPDataset (+ optional provenance sidecar)
```

## Loading from BigQuery

{py:func}`~ehr2rl.bigquery.load_mimiciv_bigquery_dataset` runs these steps:

1. **Resolve features.** The {py:class}`~ehr2rl.data.FeaturePreset` maps its
   canonical concepts to itemids through the itemid map.
2. **Validate the map.** Two queries read the live `d_items` and `d_labitems`
   label tables. {py:func}`~ehr2rl.data.itemid_maps.validate_itemid_map`
   stops the load if any itemid is missing or relabelled.
3. **Define the cohort.** {py:class}`~ehr2rl.bigquery.BigQueryCohort` builds a
   `cohort` subquery from {py:class}`~ehr2rl.bigquery.CohortCriteria`. Every
   later query joins against it, so no query reads beyond the cohort.
4. **Query.** Admissions, chartevents, labevents, and inputevents are fetched
   through the {py:class}`~ehr2rl.bigquery.GuardedBigQueryClient`, each one
   dry-run checked against `maximum_bytes_billed` and cached.
5. **Canonicalize.** Event rows are renamed from itemids to concept names.
6. **Build states.** Events are pivoted to one row per chart time per
   admission, forward-filled, and zero-filled before the first measurement.
7. **Build actions.** {py:func}`~ehr2rl.actions.build_medication_actions` turns
   inputevents into vasopressor and fluid bins at each state's timestamp.
8. **Record metadata.** Mortality, feature and action names, action sizes, and
   provenance are attached to each trajectory.

Rewards are zero at this point; nothing about the outcome is encoded in the
data until you choose a reward.

## Loading from CSV or synthetic data

The local CSV path runs steps 5 and 6 on tables read from disk, with raw itemid
features and placeholder actions. See [Local CSV loading](../use/local-csv.md).

{py:func}`~ehr2rl.make_synthetic_dataset` skips loading entirely and generates
trajectories with the same shape and metadata conventions.

## After loading

- **Rewards.** A {py:class}`~ehr2rl.reward.BaseReward` reads each trajectory's
  states, terminals, and metadata and returns a new dataset with rewards. See
  [Reward semantics](reward-semantics.md).
- **Behavior policy.** {py:class}`~ehr2rl.BehaviorPolicy` fits on all
  timesteps at once. It does not need rewards.
- **Export.** {py:func}`~ehr2rl.to_d3rlpy` concatenates all trajectories into
  one `MDPDataset` and can write a [provenance](provenance.md) sidecar.

Each step takes and returns ordinary objects, so you can inspect or modify a
dataset between any two of them.
