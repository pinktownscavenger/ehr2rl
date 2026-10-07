# Behavior policy

`BehaviorPolicy` estimates the clinicians' behavior policy: the probability of
each observed action given the patient state. Off-policy evaluation and some
offline RL methods need these probabilities.

```python
from ehr2rl import BehaviorPolicy

policy = BehaviorPolicy().fit(ds)

probabilities = policy.predict_proba(ds[0].states)  # (T, n_actions)
propensities = policy.propensity_scores(ds)         # (total timesteps,)
```

## Model

`fit` stacks every timestep in the dataset into one table of states and
action labels, then trains:

- a standardized multinomial logistic regression, or
- a constant classifier when only one action is observed.

`random_state` (default `42`) makes fitting deterministic.

## Outputs

| Method | Returns | Shape |
|---|---|---|
| `predict_proba(states)` | Probability of each action class per row | `(N, n_classes)` |
| `propensity_scores(dataset)` | Probability of the action actually taken at each step | `(total timesteps,)` |

Columns of `predict_proba` follow `policy.model.classes_`. Both methods raise
`ValueError` if called before `fit`.

Scores are computed on whatever data you pass, so propensities for the
training dataset are in-sample. Fit on one split and score another when that
matters for your estimator.

## Which action is modeled

:::{warning}
`BehaviorPolicy` models only the **first** action column. For the two-column
medication actions, that is the vasopressor bin; fluids are ignored.
:::

Action labels are derived from that column:

- If it holds at most `n_action_bins` distinct integers (default `5`), they are
  used as class labels directly.
- Otherwise it is split into at most `n_action_bins` quantile bins.

### Modeling both medication columns

Combine the columns into one joint action first, and raise `n_action_bins` to
the joint size so the joint actions are not re-binned:

```python
import numpy as np
from dataclasses import replace

from ehr2rl import BehaviorPolicy

sizes = ds[0].metadata["action_sizes"]  # for example [5, 5]
joint = ds.copy_with(
    replace(t, actions=np.ravel_multi_index(tuple(t.actions.T), sizes).reshape(-1, 1))
    for t in ds
)
policy = BehaviorPolicy(n_action_bins=int(np.prod(sizes))).fit(joint)
```

This is the same joint encoding `to_d3rlpy` uses, so class `k` here is action
`k` in the exported dataset.

:::{note}
If `propensity_scores` meets an action label that never appeared during
`fit`, it returns the probability of the first class instead. Fit on data that
covers the actions you score.
:::
