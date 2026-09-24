# Changelog

All notable changes to `ehr2rl` will be documented in this file.

## 0.2.0 - 2026-09-24

### Added

- BigQuery cohort/query tooling with dry-run budget guards and
  `maximum_bytes_billed` backstops.
- Versioned MIMIC-IV v3.1 itemid maps and canonical feature presets.
- Fluids and vasopressor medication action construction with configurable dose
  bins.
- `ReadmissionReward` and `CompositeReward`.
- Provenance sidecar export for `d3rlpy` datasets.
- Real BigQuery-to-`d3rlpy` example with a bounded cohort.

### Changed

- Real MIMIC-IV v3.1 development is now BigQuery-first.
- Local CSV loading remains backward compatible but frozen for v0.2.

### Deferred

- Minari export.
- Standalone EHR pre-flight validator.
- CLI and documentation site.
- eICU, MIMIC-III, OMOP-CDM, async loading, and additional dataset families.

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
