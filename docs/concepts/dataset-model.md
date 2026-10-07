# Dataset model

Every part of `ehr2rl` reads and returns the same two objects: a
{py:class}`~ehr2rl.PatientTrajectory` for one patient episode, and an
{py:class}`~ehr2rl.EHRDataset` holding many of them.

## Trajectories

A trajectory is a set of arrays that all share the same first dimension, `T`,
the number of timesteps.

| Field | Shape | Meaning |
|---|---|---|
| `timestamps` | `(T,)` | Unix time in seconds of each step |
| `states` | `(T, D)` | `D` features observed at each step, as floats |
| `actions` | `(T, A)` | `A` action columns taken at each step |
| `rewards` | `(T,)` | Reward at each step, as floats |
| `terminals` | `(T,)` | `True` where the episode ends |

Read row `t` across the arrays as one transition: in state `states[t]`, the
clinicians took `actions[t]`, which earned `rewards[t]`.

### Invariants

Constructing a trajectory converts every array to NumPy and checks:

- `T` is at least 1, and every array has `T` rows;
- `states` is two-dimensional;
- `rewards` and `terminals` are one-dimensional.

A one-dimensional `actions` array is reshaped to `(T, 1)`, so `actions` is
always two-dimensional. A violation raises `ValueError` immediately, so a
badly shaped trajectory cannot reach a reward function or exporter.

Every trajectory built by `ehr2rl` has exactly one terminal, at its last step.

### Identity and metadata

`subject_id` and `admission_id` hold MIMIC-IV's `subject_id` and `hadm_id` as
strings. One trajectory corresponds to one hospital admission.

`metadata` is a dictionary for everything that is not a per-step array. Reward
functions, the exporter, and you can all read and add keys. These keys have
defined meanings:

| Key | Set by | Used by |
|---|---|---|
| `died` | BigQuery, CSV, synthetic | {py:class}`~ehr2rl.MortalityReward`, {py:class}`~ehr2rl.ReadmissionReward` |
| `feature_names` | BigQuery, CSV, synthetic | You, to name `states` columns |
| `action_names` | BigQuery, synthetic (medication mode) | You, to name `actions` columns |
| `action_sizes` | BigQuery, synthetic | {py:func}`~ehr2rl.to_d3rlpy` |
| `sofa_scores` | Synthetic only | {py:class}`~ehr2rl.SofaReward` |
| `readmitted_within_30_days` | Nobody; add it yourself | {py:class}`~ehr2rl.ReadmissionReward` |
| `provenance` | BigQuery | {py:func}`~ehr2rl.to_d3rlpy` sidecars |

## Datasets

An {py:class}`~ehr2rl.EHRDataset` is a list of trajectories with `len()`,
iteration, and integer indexing:

```python
len(ds)          # number of trajectories
ds[0]            # first trajectory
for trajectory in ds:
    ...
```

Trajectories in a dataset may have different lengths, but should share the
same `D`, the same action columns, and the same metadata conventions. The
exporter and behavior policy stack them into one table.

## Copies and in-place changes

Operations follow one rule: **transformations return new objects; loaders
modify in place.**

| Operation | Effect |
|---|---|
| {py:meth}`BaseReward.shape <ehr2rl.reward.BaseReward.shape>` | Returns a new dataset; the input is unchanged |
| {py:meth}`~ehr2rl.PatientTrajectory.with_rewards` | Returns a new trajectory |
| {py:meth}`~ehr2rl.EHRDataset.copy_with` | Returns a new dataset with other trajectories |
| `load_*` and {py:meth}`~ehr2rl.EHRDataset.featurize` | Modify the dataset and return it, for chaining |

Copies are shallow. A trajectory from `with_rewards` shares its `metadata`
dictionary and its other arrays with the original, so changing
`metadata` on one changes it on both. Trajectory fields can also be assigned
directly, as the BigQuery pipeline does for `actions`; shapes are not
re-validated after direct assignment.
