# Changelog

All notable changes to `ehr2rl` will be documented in this file.

## 0.1.0 - 2026-07-29

### Added

- Initial public Python package scaffold.
- `PatientTrajectory` and `EHRDataset` core data model.
- Schema-validated MIMIC-IV-style admissions, ICU chart event, and lab event loaders.
- Synthetic trajectory generator for tests and examples.
- `MortalityReward` and `SofaReward`.
- Basic behavior policy estimator over synthetic or user-provided actions.
- Lazy `d3rlpy` export with optional dependency support.
- Synthetic-to-d3rlpy IQL smoke example.
- Pytest, Ruff, mypy, and GitHub Actions CI.

### Deferred

- Real medication/action construction.
- Full MIMIC-IV validation beyond demo schema spot checks.
- Minari export.
- Readmission and composite rewards.
- CLI and documentation site.
- eICU, MIMIC-III, and OMOP-CDM support.
