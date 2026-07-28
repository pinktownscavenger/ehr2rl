# ehr2rl

`ehr2rl` is a Python library for turning MIMIC-IV-style electronic health
record data into datasets ready for offline reinforcement learning research.
It sits between raw clinical tables and offline RL libraries such as
`d3rlpy`, handling the infrastructure work of representing patient trajectories,
building rewards, estimating observed behavior, and exporting MDP-shaped data.

This project is early and public from the start. The v0.1 goal is intentionally
narrow: synthetic-data-tested infrastructure, MIMIC-IV-style table loading,
basic rewards, a simple behavior policy estimator, and a first `d3rlpy` export.

## What v0.1 Supports

- A core `PatientTrajectory` data model.
- A chainable `EHRDataset` collection API.
- Schema-validated CSV loaders for admissions, vitals, and labs.
- Synthetic MIMIC-IV-style trajectories for tests and examples.
- `MortalityReward` and `SofaReward`.
- Basic behavior policy estimation with logistic regression.
- Lazy `d3rlpy` export via the optional `ehr2rl[d3rlpy]` extra.

## Installation

`ehr2rl` targets Python 3.10+.

From a local checkout:

```bash
pip install -e ".[dev]"
```

For `d3rlpy` export:

```bash
pip install -e ".[dev,d3rlpy]"
```

## Quickstart

```python
from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset, to_d3rlpy

ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)
policy = BehaviorPolicy().fit(ds)
ds = MortalityReward().shape(ds, policy=policy)

# Requires: pip install ehr2rl[d3rlpy]
mdp_dataset = to_d3rlpy(ds)
```

The synthetic path is the default development path so tests and examples do not
require access to MIMIC-IV.

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

v0.1 focuses on one dataset family and one export target. Future work may add
medication-specific action construction, real MIMIC-IV validation passes,
readmission/composite rewards, Minari export, CLI tooling, documentation, and
support for eICU, MIMIC-III, or OMOP-CDM.
