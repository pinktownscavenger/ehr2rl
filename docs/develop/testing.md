# Testing

The test suite runs without MIMIC-IV access, cloud credentials, or network
access. Real data is replaced by synthetic trajectories and a fake BigQuery
client.

```bash
pytest
```

Tests live in `tests/`, one file per feature area, such as
`test_medication_actions.py` or `test_bigquery_pipeline.py`.

## Conventions

- **Synthetic data first.** Use
  {py:func}`~ehr2rl.make_synthetic_dataset` with a fixed `seed` for any test
  that needs a dataset. Pass `include_medication_metadata=True` for
  two-column medication actions.
- **Fake the BigQuery client, not BigQuery.** `tests/test_bigquery_pipeline.py`
  defines `FakeGuardedClient`, which returns prepared DataFrames by matching
  the SQL it receives. Pipeline tests use it to exercise the real loader end to
  end. Use it rather than mocking `google.cloud.bigquery`.
- **Skip on missing extras.** Tests that need `d3rlpy` start with
  `pytest.importorskip("d3rlpy")`, so a plain `.[dev]` install still passes.
- **Cohorts larger than one.** Bugs that only appear across trajectories, such
  as mismatched metadata, need at least two patients. Prefer small multi-patient
  fixtures.
- **Assert behavior and error messages.** Use `pytest.raises(..., match=...)`
  so a test fails if the wrong error is raised.

## Test families

| Area | Files |
|---|---|
| Data model and CSV path | `test_data.py`, `test_featurize_canonical.py` |
| Itemid maps and presets | `test_itemid_maps.py`, `test_feature_presets.py` |
| BigQuery | `test_bigquery_cohort.py`, `test_bigquery_client.py`, `test_bigquery_pipeline.py`, `test_bigquery_smoke.py` |
| Actions | `test_medication_actions.py`, `test_actions_vasopressors.py` |
| Rewards | `test_reward.py`, `test_composite_reward.py`, `test_readmission_reward.py` |
| Policy, export, provenance | `test_policy.py`, `test_export.py`, `test_provenance.py` |
| Synthetic data and examples | `test_synthetic.py`, `test_examples.py` |
| Public API documentation | `test_public_docs.py` |

`test_public_docs.py` holds the list of supported public objects. It checks
that each is exported in `__all__` and has a descriptive docstring, and the
documentation tests use the same list.

## Documentation tests

The site has its own tests in `docs/tests/`, which build the site strictly and
inspect the HTML. They need the `docs` extra and are not part of the default
`pytest` run:

```bash
.venv-docs/bin/python -m pytest docs/tests
```

See [Documentation workflow](documentation.md).
