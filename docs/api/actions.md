# Actions

See [Medication actions](../use/actions.md) for how doses are aggregated and
binned.

```{eval-rst}
.. autoclass:: ehr2rl.actions.ActionConfig
```

```{eval-rst}
.. autoclass:: ehr2rl.actions.DoseBins
   :members: n_bins, assign
```

```{eval-rst}
.. autofunction:: ehr2rl.actions.build_medication_actions
```

## Norepinephrine equivalents

```{eval-rst}
.. autoclass:: ehr2rl.actions.VasopressorConversion
```

```{eval-rst}
.. autodata:: ehr2rl.actions.DEFAULT_NEE_CONVERSIONS
   :no-value:
```

```{eval-rst}
.. autofunction:: ehr2rl.actions.norepinephrine_equivalent
```
