import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("EHR2RL_RUN_BIGQUERY_SMOKE") != "1",
    reason="set EHR2RL_RUN_BIGQUERY_SMOKE=1 to run the MIMIC-IV BigQuery smoke test",
)


def test_mimiciv_bigquery_smoke_builds_bounded_dataset():
    from ehr2rl.data.bigquery import load_mimiciv_smoke_dataset

    ds = load_mimiciv_smoke_dataset(
        billing_project="physionet-data-503819",
        cohort_size=25,
        maximum_bytes_billed=25_000_000_000,
    )

    assert 0 < len(ds) <= 25
    assert ds[0].states.shape[0] == ds[0].actions.shape[0]
    assert ds[0].states.shape[1] >= 1
    assert ds[0].terminals[-1]
    assert ds[0].metadata["bigquery_source"]["cohort_size"] == 25
