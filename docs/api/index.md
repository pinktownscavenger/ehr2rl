# API reference

Every object here is part of the supported public API, listed under the import
path to use. Anything not listed is internal and may change without notice.

| Page | Import from | Contents |
|---|---|---|
| [Core](core.md) | `ehr2rl` | `PatientTrajectory`, `EHRDataset`, `EHRValidationError` |
| [Synthetic data](synthetic.md) | `ehr2rl` | `make_synthetic_dataset` |
| [Features and itemids](features.md) | `ehr2rl.data`, `ehr2rl.data.itemid_maps` | Presets and itemid maps |
| [BigQuery](bigquery.md) | `ehr2rl.bigquery` | Cohorts, guarded client, loader, errors |
| [Actions](actions.md) | `ehr2rl.actions` | Dose bins and medication actions |
| [Rewards](rewards.md) | `ehr2rl`, `ehr2rl.reward` | Reward base class and built-in rewards |
| [Policy](policy.md) | `ehr2rl` | `BehaviorPolicy` |
| [Export](export.md) | `ehr2rl` | `to_d3rlpy` |
| [Provenance](provenance.md) | `ehr2rl.provenance` | Provenance sidecars |

```{toctree}
:hidden:

core
synthetic
features
bigquery
actions
rewards
policy
export
provenance
```
