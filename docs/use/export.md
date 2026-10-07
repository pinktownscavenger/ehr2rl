# Export to d3rlpy

`to_d3rlpy` converts an `EHRDataset` into a
[`d3rlpy`](https://d3rlpy.readthedocs.io/) `MDPDataset` for offline RL
training.

```bash
pip install "ehr2rl[d3rlpy]"
```

```python
from ehr2rl import MortalityReward, make_synthetic_dataset, to_d3rlpy

ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)
ds = MortalityReward().shape(ds)

mdp_dataset = to_d3rlpy(ds)
```

Without the extra installed, `to_d3rlpy` raises an `ImportError` that names it.

## What is exported

All trajectories are concatenated. Each trajectory becomes one episode, ending
where `terminals` is `True`.

| Array | Shape | dtype |
|---|---|---|
| observations | `(N, D)` | `float32` |
| actions | `(N, 1)` discrete, or `(N, A)` continuous | `int64` or float |
| rewards | `(N,)` | `float32` |
| terminals | `(N,)` | `float32` |

`N` is the total number of timesteps across trajectories. Every trajectory
ends in a true terminal, not a timeout, including discharges.

## Discrete and continuous actions

The action type decides how actions are exported:

| Actions | `metadata["action_sizes"]` | Exported as |
|---|---|---|
| Integers, one column | present | Discrete, with `action_size` from metadata |
| Integers, several columns | present | **One joint discrete action**, `action_size` = product of sizes |
| Integers, one column | absent | Discrete, with size inferred by `d3rlpy` from the data |
| Integers, several columns | absent | `ValueError` |
| Floats | ignored | Continuous, unchanged |

The BigQuery pipeline and the synthetic generator both record
`action_sizes`, so their actions export with the full action space, including
actions that never occur in the data.

### Joint medication actions

Two-column medication actions become one index in row-major order:
`joint = vasopressor_bin * n_fluid_bins + fluid_bin`. With five bins each there
are 25 joint actions. Recover the bins from a learned action with NumPy:

```python
import numpy as np

sizes = ds[0].metadata["action_sizes"]          # for example [5, 5]
vasopressor_bin, fluid_bin = np.unravel_index(action, sizes)
```

Use a **discrete-action** algorithm such as `DiscreteCQL` or `DiscreteBCQ`:

```python
import d3rlpy

algorithm = d3rlpy.algos.DiscreteCQLConfig().create(device="cpu:0")
algorithm.fit(mdp_dataset, n_steps=10_000)
```

Continuous algorithms such as `IQL` and `CQL` reject discrete datasets.

Export raises `ValueError` if trajectories declare different `action_sizes`,
or if an action falls outside its declared size.

## Provenance sidecar

Datasets from BigQuery can be exported with a JSON record of how they were
built:

```python
mdp_dataset = to_d3rlpy(ds, provenance_path="dataset.provenance.json")
```

The sidecar contains the BigQuery job IDs, combined query hash, itemid map
version, feature preset, extraction timestamp, and MIMIC-IV version. Read it
back with `ehr2rl.provenance.read_provenance`.

Every trajectory must carry the same `metadata["provenance"]`. Synthetic data
has none, so passing `provenance_path` for it raises `TypeError`.

## Before you train

- Check for `NaN` rewards, for example from censored
  [readmission rewards](rewards.md).
- Synthetic data is for development only. Results on it say nothing about
  clinical behavior.
