# Synthetic quickstart

This walkthrough builds a small offline RL dataset from synthetic MIMIC-IV-style
data. It needs only the [base install](installation.md): no MIMIC-IV access, no
cloud credentials, and no `d3rlpy`.

## The complete script

```{literalinclude} ../../examples/docs_quickstart.py
:language: python
```

This is `examples/docs_quickstart.py` from the repository, shown exactly as the
test suite runs it, so the output below is what you should see:

```text
['heart_rate', 'mean_bp', 'lactate', 'creatinine']
(24, 4)
(24, 1)
(600, 2)
1.0
{'n_trajectories': 25, 'state_shape': (24, 4), 'probability_rows': 600}
```

## What each step does

### 1. Generate trajectories

`make_synthetic_dataset` returns an `EHRDataset`: a list of `PatientTrajectory`
objects, one per synthetic ICU stay. Data are deterministic for a given `seed`.

Each trajectory holds aligned arrays, where `T` is the number of timesteps:

| Field | Shape | Contents |
|---|---|---|
| `timestamps` | `(T,)` | Unix seconds, one hour apart |
| `states` | `(T, D)` | Heart rate, mean blood pressure, lactate, creatinine |
| `actions` | `(T, A)` | One column: `1` when mean blood pressure is below 65, else `0` |
| `rewards` | `(T,)` | All zero until a reward is applied |
| `terminals` | `(T,)` | `True` only at the last step |

`metadata` carries the feature names, whether the patient died, and a synthetic
SOFA score series for `SofaReward`.

### 2. Estimate the behavior policy

`BehaviorPolicy().fit(ds)` learns the probability of each observed action given
the state. `predict_proba` returns one row per state and one column per action
class, so stacking all 25 × 24 states gives shape `(600, 2)`.

### 3. Shape rewards

`MortalityReward().shape(ds)` returns a **new** dataset whose trajectories carry
`+1` at the terminal step for survivors and `-1` for in-hospital deaths. The
original dataset is not modified.

## Next steps

- Export to `d3rlpy` with `pip install "ehr2rl[d3rlpy]"` and `to_d3rlpy(ds)`.
- Use two-column medication actions in synthetic data with
  `make_synthetic_dataset(include_medication_metadata=True)`.
