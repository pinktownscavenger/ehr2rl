import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("EHR2RL_RUN_BIGQUERY_SMOKE") != "1",
    reason="set EHR2RL_RUN_BIGQUERY_SMOKE=1 to run the MIMIC-IV BigQuery smoke test",
)


def test_mimiciv_bigquery_smoke_builds_bounded_dataset():
    from google.cloud import bigquery

    from ehr2rl.actions import ActionConfig, DoseBins
    from ehr2rl.bigquery import (
        BigQueryCohort,
        CohortCriteria,
        GuardedBigQueryClient,
        load_mimiciv_bigquery_dataset,
    )
    from ehr2rl.data.itemid_maps import load_itemid_map
    from ehr2rl.data.presets import get_feature_preset

    billing_project = os.getenv("EHR2RL_BIGQUERY_BILLING_PROJECT", "physionet-data-503819")
    client = GuardedBigQueryClient(
        bigquery.Client(project=billing_project),
        maximum_bytes_billed=25_000_000_000,
    )
    ds = load_mimiciv_bigquery_dataset(
        client=client,
        cohort=BigQueryCohort(CohortCriteria(cohort_size=25)),
        preset=get_feature_preset("vitals_only"),
        itemid_map=load_itemid_map("v3_1"),
        action_config=ActionConfig(
            vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3, 0.6)),
            fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0, 1000.0)),
        ),
    )

    assert 0 < len(ds) <= 25
    assert ds[0].states.shape[0] == ds[0].actions.shape[0]
    assert ds[0].actions.shape[1] == 2
    assert ds[0].states.shape[1] >= 1
    assert ds[0].terminals[-1]
    assert ds[0].metadata["provenance"]["itemid_map_version"] == "v3_1"
