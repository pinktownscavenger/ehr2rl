# Rewards

A reward function computes one value per timestep for each trajectory.
Rewards start at zero and are filled in by calling `shape`:

```python
from ehr2rl import MortalityReward

ds = MortalityReward().shape(ds)
```

`shape` returns a **new** dataset. The input dataset and its trajectories are
not modified.

:::{important}
Reward design is a research decision with clinical consequences. These
classes implement common definitions from the literature; they do not make a
reward clinically valid for your question.
:::

## Built-in rewards

### `MortalityReward`

A terminal reward for in-hospital survival.

```python
MortalityReward(survival_reward=1.0, death_penalty=-1.0)
```

- Needs `metadata["died"]`. A missing key is treated as survival.
- The reward is placed at the last timestep where `terminals` is `True`; all
  other steps are `0`.
- The BigQuery pipeline and the synthetic generator both set `died`.

### `SofaReward`

A dense reward for change in SOFA score: improvement is positive.

```python
SofaReward(clip=(-5.0, 5.0))
```

- Needs `metadata["sofa_scores"]` with shape `(T,)`.
- `reward[t] = sofa[t - 1] - sofa[t]`, and `reward[0] = 0`.
- Rewards are clipped to `clip`; pass `clip=None` to disable.
- Synthetic data includes SOFA scores. **The BigQuery pipeline does not**:
  compute them yourself and add them to each trajectory's metadata.

### `ReadmissionReward`

A terminal reward for 30-day readmission.

```python
ReadmissionReward(
    readmitted_reward=-1.0,
    not_readmitted_reward=1.0,
    censored_value=float("nan"),
)
```

- Needs `metadata["readmitted_within_30_days"]`: `True`, `False`, or `None`
  when follow-up is censored. A missing key raises `ValueError`.
- The reward is placed at the final timestep.
- Patients who died get `0`, regardless of readmission.
- Neither the BigQuery pipeline nor the synthetic generator sets this key.

:::{warning}
The default `censored_value` is `NaN`, and NaN rewards are exported unchanged
to `d3rlpy`, where they corrupt training. Either set `censored_value` to a
number or drop censored trajectories before exporting.
:::

The `window_days` argument is stored but not used: the window is fixed by the
metadata key you provide.

### `CompositeReward`

A weighted sum of other rewards:

```python
from ehr2rl import CompositeReward, MortalityReward, SofaReward

reward = CompositeReward([
    (MortalityReward(), 1.0),
    (SofaReward(), 0.1),
])
ds = reward.shape(ds)
```

Each component must return shape `(T,)`, or `ValueError` names the one that
did not.

## Writing your own reward

Subclass `BaseReward` and implement `compute`, which receives one
`PatientTrajectory` and returns an array of shape `(T,)`:

```python
import numpy as np

from ehr2rl.reward import BaseReward


class LactateClearanceReward(BaseReward):
    """Reward falling lactate between consecutive steps."""

    def __init__(self, column: int) -> None:
        self.column = column

    def compute(self, trajectory):
        lactate = trajectory.states[:, self.column]
        rewards = np.zeros(trajectory.n_steps)
        rewards[1:] = lactate[:-1] - lactate[1:]
        return rewards
```

`shape` and `CompositeReward` then work with it unchanged. Look up state
columns by name with `trajectory.metadata["feature_names"].index("lactate")`.

`shape(dataset, policy=...)` accepts a `policy` argument for future
policy-dependent rewards, but no built-in reward uses it.
