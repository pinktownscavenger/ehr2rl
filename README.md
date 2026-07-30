# ehr2rl

`ehr2rl` is a Python library for turning MIMIC-IV-style electronic health record
data into datasets ready for offline reinforcement learning research.

Healthcare ML libraries are usually built for supervised prediction, while
offline RL libraries expect a clean state-action-reward dataset that already
exists. `ehr2rl` fills the gap between those worlds: loading longitudinal EHR
tables, representing patient trajectories, shaping rewards, estimating observed
behavior, and exporting data for tools such as `d3rlpy`.

## What v0.1 Supports

- A core `PatientTrajectory` data model.
- A chainable `EHRDataset` collection API.
- Schema-validated CSV loaders for admissions, vitals, and labs.
- Synthetic MIMIC-IV-style trajectories for tests and examples.
- `MortalityReward` and `SofaReward`.
- Basic behavior policy estimation with logistic regression over synthetic or
  user-provided actions.
- Lazy `d3rlpy` export via the optional `ehr2rl[d3rlpy]` extra.

## Installation

`ehr2rl` targets Python 3.10+.

Minimal install:

```bash
pip install ehr2rl
```

For `d3rlpy` export:

```bash
pip install "ehr2rl[d3rlpy]"
```

## Quickstart

```python
from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset, to_d3rlpy

ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)

# v0.1 uses synthetic/user-provided actions. Real medication action construction
# is planned for v0.2.
for trajectory in ds:
    mean_bp = trajectory.states[:, 1]
    trajectory.actions = ((140.0 - mean_bp) / 105.0).reshape(-1, 1)

policy = BehaviorPolicy().fit(ds)
ds = MortalityReward().shape(ds, policy=policy)

# Requires: pip install ehr2rl[d3rlpy]
mdp_dataset = to_d3rlpy(ds)
```

The synthetic path is the default development path so tests and examples do not
require access to MIMIC-IV.

## Development Install

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy ehr2rl
```

## MIMIC-IV Access

`ehr2rl` does not ship, mirror, or provide access to MIMIC-IV. Researchers must
obtain any clinical data through the appropriate credentialed channels, such as
PhysioNet, and comply with the applicable data use agreements.

## Clinical Disclaimer

`ehr2rl` is research infrastructure. It is not clinical decision support, does
not validate treatment recommendations, and does not define a clinically
authoritative reward function. Reward design and interpretation remain the
responsibility of the researcher.

## Roadmap

v0.2 priorities:

- Medication-specific action construction.
- Real MIMIC-IV validation passes beyond the public demo schema.
- Readmission and composite rewards.
- Minari export.
- CLI tooling and a documentation site.
- Additional dataset families such as eICU, MIMIC-III, and OMOP-CDM.

## Contributing

Issues and pull requests are welcome. For v0.1, the most useful contributions
are schema checks, synthetic-data edge cases, documentation fixes, and small
export compatibility improvements.

## Citation

Citation metadata will be added once the project has a stable archival release.
