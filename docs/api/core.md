# Core

Trajectories and datasets are the shared representation every other part of
`ehr2rl` reads and returns. See [the synthetic quickstart](../use/synthetic-quickstart.md)
for a walkthrough.

```{eval-rst}
.. autoclass:: ehr2rl.PatientTrajectory
   :members: n_steps, with_rewards
```

```{eval-rst}
.. autoclass:: ehr2rl.EHRDataset
   :members: copy_with, load_admissions, load_vitals, load_labs, featurize
```

The `load_*` and `featurize` methods implement the frozen
[local CSV path](../use/local-csv.md).

```{eval-rst}
.. autoexception:: ehr2rl.EHRValidationError
```
