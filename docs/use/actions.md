# Medication actions

The BigQuery pipeline turns ICU `inputevents` into two discrete actions per
timestep: a **vasopressor dose bin** and an **IV fluid volume bin**. Actions
have shape `(T, 2)` and are stored as integers.

## Configure the bins

```python
from ehr2rl.actions import ActionConfig, DoseBins

config = ActionConfig(
    vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3, 0.6)),       # mcg/kg/min NEE
    fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0, 1000.0)),      # mL per timestep
)
```

| Field | Default | Meaning |
|---|---|---|
| `vasopressor_bins` | required | Bins for norepinephrine-equivalent dose in mcg/kg/min |
| `fluid_bins` | required | Bins for fluid volume in mL within one timestep |
| `timestep` | `"1h"` | Window each action is aggregated over |
| `status_include` | `("FinishedRunning", "Changed")` | `statusdescription` values to keep; others (for example `Paused`) are ignored |

## How dose bins work

Bin `0` means no dose: any value at or below zero. Positive values are placed
by the edges, and a value exactly on an edge goes into the **higher** bin.

```python
bins = DoseBins(edges=(0.0, 0.1, 0.3, 0.6))
bins.assign([0.0, 0.05, 0.1, 0.29, 0.3, 0.6, 2.0])  # [0, 1, 2, 2, 3, 4, 4]
bins.n_bins                                           # 5
```

| Bin | Vasopressor NEE (mcg/kg/min) |
|---|---|
| 0 | none |
| 1 | above 0 and below 0.1 |
| 2 | 0.1 to below 0.3 |
| 3 | 0.3 to below 0.6 |
| 4 | 0.6 or more |

`DoseBins(edges, labels=...)` relabels the bins; `labels` needs
`len(edges) + 1` integers. `n_bins` is the number of distinct values `assign`
can return, which the exporter uses as the action-space size.

## How doses are aggregated

Each state timestamp is floored to `timestep`. For each window:

- **Vasopressors:** the **maximum** norepinephrine-equivalent rate of any
  infusion overlapping the window, so a short high-dose infusion is not
  diluted.
- **Fluids:** each event's recorded volume is spread evenly over its duration,
  and the window gets the share that overlaps it. A 1,000 mL infusion over two
  hours contributes 500 mL to each hour.

Because BigQuery states use irregular chart times, several states in the same
hour share that hour's action.

## Norepinephrine equivalents

Vasopressors are converted to one scale before binning. Each row's recorded
rate unit (`rateuom`) is first converted to the unit the factor applies to:

| Drug | itemid | Factor | Factor applies to |
|---|---|---|---|
| Norepinephrine | 221906 | 1.0 | mcg/kg/min |
| Epinephrine | 221289 | 1.0 | mcg/kg/min |
| Vasopressin | 222315 | 2.5 | units/min |
| Phenylephrine | 221749 | 0.1 | mcg/kg/min |
| Dopamine | 221662 | 0.01 | mcg/kg/min |

Recognized units are `mcg/kg/min`, `mg/kg/min`, `mcg/min`, `mg/min`,
`units/min`, and `units/hour`. Per-minute rates without a weight are divided by
the row's `patientweight`. For example, vasopressin at 2.4 units/hour is
0.04 units/min, or 0.1 mcg/kg/min NEE.

:::{warning}
A vasopressor row with any other unit, or a per-minute rate without a positive
`patientweight`, raises `ValueError` rather than producing a dose in the wrong
unit.
:::

These factors are a common research convention, not a clinical standard.
Supply your own with `VasopressorConversion` and
`norepinephrine_equivalent(row, conversions=...)`.

## Fluids

Fluid volume comes from the `amount` column of two itemids: 225158 (NaCl 0.9%)
and 220949 (Dextrose 5%). Other fluids are not counted.

## Building actions directly

`build_medication_actions` works on any `inputevents`-shaped DataFrame, which
is useful for testing bin choices without BigQuery:

```python
import numpy as np
import pandas as pd

from ehr2rl.actions import build_medication_actions

timestamps = np.array([
    pd.Timestamp("2026-01-01 00:00").timestamp(),
    pd.Timestamp("2026-01-01 01:00").timestamp(),
])
events = pd.DataFrame({
    "starttime": ["2026-01-01 00:30", "2026-01-01 00:00"],
    "endtime": ["2026-01-01 01:30", "2026-01-01 02:00"],
    "itemid": [221906, 225158],        # norepinephrine, NaCl 0.9%
    "rate": [0.2, 0.0],
    "rateuom": ["mcg/kg/min", None],
    "amount": [0.0, 1000.0],
    "statusdescription": ["FinishedRunning", "FinishedRunning"],
})

build_medication_actions(events, timestamps, config=config)
# [[2, 3], [2, 3]]: NEE 0.2 in both hours; 500 mL of fluid in each hour
```

## Synthetic actions

`make_synthetic_dataset(include_medication_metadata=True)` produces the same
two-column shape with two bins each, so you can develop against it without
credentials. By default the synthetic generator uses a single binary action.

## Training on these actions

Two integer columns are not a format RL libraries accept directly. See
[Export to d3rlpy](export.md) for how they become one discrete action, and
[Behavior policy](behavior-policy.md) for estimating both columns together.
