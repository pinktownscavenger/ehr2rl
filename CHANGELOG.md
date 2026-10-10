# Changelog

All notable changes to `ehr2rl` will be documented in this file.

## Unreleased

### Fixed

- `to_d3rlpy` now exports two-column medication actions as one discrete joint
  action with the full declared action space (`vasopressor_bins.n_bins *
  fluid_bins.n_bins`). Previously d3rlpy inferred a wrong action size, so
  continuous algorithms rejected the dataset and discrete algorithms crashed.
- Vasopressin norepinephrine equivalents were about 60 times too high:
  MIMIC-IV records vasopressin in units/hour, but the 2.5 factor applies per
  unit/min. Recorded `rateuom` is now converted before the factor is applied,
  including weight-normalizing mcg/min rates with `patientweight`.
- BigQuery datasets with more than one admission could not be exported with a
  provenance sidecar: each trajectory got its own extraction timestamp, so
  `to_d3rlpy(..., provenance_path=...)` rejected them as mismatched. Provenance
  is now computed once per load.

### Changed

- Vasopressor rows with a rate unit that cannot be converted now raise
  `ValueError` instead of producing a dose in the wrong unit.
- Multi-column integer actions without `metadata["action_sizes"]` now raise
  `ValueError` on export instead of producing an untrainable dataset.
- The BigQuery inputevents query also selects `rateuom` and `patientweight`,
  which changes its cache key, so cached inputevents results are re-queried once.
- `examples/bigquery_to_d3rlpy.py` trains `DiscreteCQL` instead of `IQL`.
- `ehr2rl.data.itemid_maps` and `ehr2rl.provenance` define `__all__`, so
  `import *` from them now brings in only their public names.
- Export errors about `metadata["action_sizes"]` now say how to fix them.

### Added

- `DoseBins.n_bins` and `VasopressorConversion.rate_unit` (default
  `"mcg/kg/min"`).
- Trajectories from the BigQuery pipeline and the synthetic generator record
  `metadata["action_sizes"]`; BigQuery trajectories also record
  `metadata["action_names"]`.
- Documentation site at <https://pinktownscavenger.github.io/ehr2rl/>, with
  guides, concepts, contributor docs, and an API reference. It is built with
  Sphinx, MyST, and Furo, deployed from `main` by GitHub Actions, and its
  external links are checked weekly.
- The documentation site navigates between pages without reloading, shows
  search results while typing, and tracks the section being read.
- Descriptive NumPy-style docstrings for every public API object.

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
