# Architecture

`ehr2rl` is a small package organized by stage of the pipeline. Each
subpackage owns one stage and exchanges data with the others only through
{py:class}`~ehr2rl.EHRDataset` and {py:class}`~ehr2rl.PatientTrajectory`. See
[Pipeline](../concepts/pipeline.md) for the data flow.

## Package layout

| Package | Owns | Key modules |
|---|---|---|
| `ehr2rl.data` | Trajectories, datasets, CSV loading and alignment, state construction, feature presets, itemid maps | `dataset.py`, `featurize.py`, `presets.py`, `itemid_maps.py`, `itemid_maps/v3_1.yaml` |
| `ehr2rl.bigquery` | Bounded cohort SQL, guarded query execution, assembling real datasets | `cohort.py`, `client.py`, `pipeline.py`, `errors.py` |
| `ehr2rl.actions` | Medication aggregation, vasopressor dose conversion, dose discretization | `medications.py`, `vasopressors.py`, `fluids.py`, `discretize.py` |
| `ehr2rl.reward` | The `BaseReward` interface and concrete rewards | `base.py`, `mortality.py`, `sofa.py`, `readmission.py`, `composite.py` |
| `ehr2rl.policy` | Estimating observed action probabilities | `behavior.py` |
| `ehr2rl.export` | Adapting datasets to external RL libraries | `d3rlpy.py` |
| `ehr2rl.testing` | Credential-free synthetic data | `synthetic.py` |
| `ehr2rl.provenance` | Provenance records and sidecar files | `provenance.py` |

The built-in itemid map is JSON stored with a `.yaml` extension and shipped as
package data.

## Dependency direction

Dependencies point one way, from assembly toward the core:

```text
bigquery ──► actions ──► (pandas, numpy)
   │
   └──► data ◄── reward, policy, export, testing
               export ──► provenance
```

- `data` imports nothing else from `ehr2rl` except its own modules.
- `reward`, `policy`, `export`, and `testing` depend only on `data` (and
  `export` on `provenance`). They never import `bigquery`.
- `bigquery` is the only package that combines stages.

Keep it this way: a new reward or exporter should not need anything from
`bigquery`.

## Optional dependencies

`d3rlpy` and the Google Cloud packages are optional extras. They are imported
inside the functions that need them, never at module level, so
`import ehr2rl` and every submodule work on a base install. The documentation
build relies on this: it imports every public object without either extra.

When a function needs an optional package, catch `ImportError` and re-raise
with the extra to install, as {py:func}`~ehr2rl.to_d3rlpy` does.

## Public API

The supported API is exactly what the `__all__` lists export, at the import
paths shown in the [API reference](../api/index.md). Everything else,
including modules without an underscore prefix, is internal.

- `ehr2rl/__init__.py` re-exports the most used objects.
- Each subpackage's `__init__.py` lists its own public objects.
- `ehr2rl.data.itemid_maps` and `ehr2rl.provenance` are public modules with
  their own `__all__`.
