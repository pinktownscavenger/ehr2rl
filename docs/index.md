# ehr2rl

`ehr2rl` turns MIMIC-IV-style electronic health record data into datasets ready
for offline reinforcement learning research. It loads longitudinal EHR tables,
represents patient trajectories, shapes rewards, estimates observed clinician
behavior, and exports data for tools such as `d3rlpy`.

```bash
pip install ehr2rl
```

## Synthetic quickstart

This example needs only the base install. No MIMIC-IV access or cloud
credentials are required. The [full quickstart](use/synthetic-quickstart.md)
explains each step.

```python
from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset

ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)
policy = BehaviorPolicy().fit(ds)
ds = MortalityReward().shape(ds)

print(f"{len(ds)} trajectories")                    # 25 trajectories
print(ds[0].states.shape)                           # (24, 4)
print(policy.predict_proba(ds[0].states).shape)     # (24, 2)
```

## Where to go next

::::{container} role-links

:::{container} role-link
### Researchers

Build datasets for offline RL experiments.

- [Installation and optional extras](use/installation.md)
- [MIMIC-IV v3.1 through BigQuery](use/bigquery.md), with cost guards
- [Actions](use/actions.md), [rewards](use/rewards.md),
  [behavior policy](use/behavior-policy.md), and [export](use/export.md)
- [Dataset model](concepts/dataset-model.md), [provenance](concepts/provenance.md),
  and [limitations](concepts/limitations.md)
:::

:::{container} role-link
### Contributors

Maintain and extend the library.

- Development setup and quality checks
- Architecture and data flow
- Testing conventions
- Adding features, actions, rewards, and exporters
:::

::::

Both paths share one [API reference](api/index.md).

[GitHub](https://github.com/pinktownscavenger/ehr2rl) ·
[PyPI](https://pypi.org/project/ehr2rl/) ·
[Issues](https://github.com/pinktownscavenger/ehr2rl/issues)

:::{important}
`ehr2rl` is research infrastructure. It is not clinical decision support and
does not validate treatment recommendations. It does not ship or provide access
to MIMIC-IV: obtain clinical data through credentialed channels such as
PhysioNet and follow the applicable data use agreements.
:::

```{toctree}
:hidden:
:caption: Get started

use/installation
use/synthetic-quickstart
```

```{toctree}
:hidden:
:caption: Use ehr2rl

use/bigquery
use/actions
use/rewards
use/behavior-policy
use/export
use/local-csv
```

```{toctree}
:hidden:
:caption: Understand

concepts/dataset-model
concepts/pipeline
concepts/features-and-itemids
concepts/reward-semantics
concepts/provenance
concepts/limitations
```

```{toctree}
:hidden:
:caption: Reference

api/index
```
