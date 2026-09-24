import pandas as pd
import pytest


class FakeGuardedClient:
    def __init__(self, tables):
        self.tables = tables
        self.calls = []

    def query_dataframe(self, sql, *, cache_key_parts=()):
        from ehr2rl.bigquery import QueryResult

        self.calls.append((sql, cache_key_parts))
        if "d_items" in sql:
            name = "icu_labels"
        elif "d_labitems" in sql:
            name = "lab_labels"
        elif "chartevents" in sql:
            name = "vitals"
        elif "labevents" in sql:
            name = "labs"
        elif "inputevents" in sql:
            name = "inputevents"
        elif ".admissions" in sql:
            name = "admissions"
        else:
            raise AssertionError(f"unexpected SQL: {sql}")
        return QueryResult(
            dataframe=self.tables[name],
            job_id=f"job_{name}",
            bytes_processed=10,
            query_hash=f"hash_{name}",
        )


def test_bigquery_pipeline_builds_dataset_from_mocked_tables():
    from ehr2rl.bigquery import (
        BigQueryCohort,
        CohortCriteria,
        load_mimiciv_bigquery_dataset,
    )

    ds = load_mimiciv_bigquery_dataset(
        client=_fake_client(),
        cohort=BigQueryCohort(CohortCriteria(cohort_size=1)),
        preset=_test_preset(),
        itemid_map=_test_itemid_map(),
        action_config=_test_action_config(),
    )

    assert len(ds) == 1
    assert ds[0].metadata["feature_names"] == ["heart_rate"]
    assert ds[0].metadata["provenance"]["itemid_map_version"] == "v3_1"


def test_bigquery_pipeline_attaches_query_hashes_and_job_ids():
    from ehr2rl.bigquery import (
        BigQueryCohort,
        CohortCriteria,
        load_mimiciv_bigquery_dataset,
    )

    ds = load_mimiciv_bigquery_dataset(
        client=_fake_client(),
        cohort=BigQueryCohort(CohortCriteria(cohort_size=1)),
        preset=_test_preset(),
        itemid_map=_test_itemid_map(),
        action_config=_test_action_config(),
    )

    provenance = ds[0].metadata["provenance"]

    assert provenance["bigquery_job_ids"] == [
        "job_admissions",
        "job_vitals",
        "job_inputevents",
    ]
    assert provenance["query_hash"] == "hash_admissions:hash_vitals:hash_inputevents"


def test_bigquery_pipeline_validates_itemid_labels_before_extraction():
    from ehr2rl.bigquery import (
        BigQueryCohort,
        CohortCriteria,
        load_mimiciv_bigquery_dataset,
    )

    fake_client = _fake_client()

    load_mimiciv_bigquery_dataset(
        client=fake_client,
        cohort=BigQueryCohort(CohortCriteria(cohort_size=1)),
        preset=_test_preset(),
        itemid_map=_test_itemid_map(),
        action_config=_test_action_config(),
    )

    queried_sql = "\n".join(sql for sql, _ in fake_client.calls)

    assert "d_items" in queried_sql
    assert "d_labitems" in queried_sql


def test_bigquery_pipeline_rejects_label_drift():
    from ehr2rl.bigquery import (
        BigQueryCohort,
        CohortCriteria,
        load_mimiciv_bigquery_dataset,
    )
    from ehr2rl.data.loaders import EHRValidationError

    fake_client = _fake_client()
    fake_client.tables["icu_labels"] = pd.DataFrame(
        {
            "itemid": [220045, 221906],
            "label": ["Heart Rhythm", "Norepinephrine"],
        }
    )

    with pytest.raises(EHRValidationError, match="label changed"):
        load_mimiv = load_mimiciv_bigquery_dataset
        load_mimiv(
            client=fake_client,
            cohort=BigQueryCohort(CohortCriteria(cohort_size=1)),
            preset=_test_preset(),
            itemid_map=_test_itemid_map(),
            action_config=_test_action_config(),
        )


def _fake_client():
    return FakeGuardedClient(
        {
            "admissions": pd.DataFrame(
                {
                    "subject_id": [1],
                    "hadm_id": [10],
                    "admittime": pd.to_datetime(["2026-01-01 00:00:00"]),
                    "dischtime": pd.to_datetime(["2026-01-01 02:00:00"]),
                    "hospital_expire_flag": [0],
                }
            ),
            "vitals": pd.DataFrame(
                {
                    "subject_id": [1],
                    "hadm_id": [10],
                    "charttime": pd.to_datetime(["2026-01-01 00:00:00"]),
                    "itemid": [220045],
                    "valuenum": [80.0],
                }
            ),
            "labs": pd.DataFrame(columns=["subject_id", "hadm_id", "charttime", "itemid", "valuenum"]),
            "inputevents": pd.DataFrame(
                columns=["starttime", "endtime", "itemid", "rate", "amount", "statusdescription"]
            ),
            "icu_labels": pd.DataFrame(
                {
                    "itemid": [220045, 221906],
                    "label": ["Heart Rate", "Norepinephrine"],
                }
            ),
            "lab_labels": pd.DataFrame({"itemid": [50813], "label": ["Lactate"]}),
        }
    )


def _test_preset():
    from ehr2rl.data.presets import FeaturePreset

    return FeaturePreset(name="vitals_only", concepts=("heart_rate",))


def _test_itemid_map():
    from ehr2rl.data.itemid_maps import ItemIdEntry, ItemIdMap

    return ItemIdMap(
        version="v3_1",
        concepts={
            "heart_rate": [
                ItemIdEntry(itemid=220045, source="chartevents", label="Heart Rate")
            ],
            "norepinephrine": [
                ItemIdEntry(itemid=221906, source="inputevents", label="Norepinephrine")
            ],
            "lactate": [
                ItemIdEntry(itemid=50813, source="labevents", label="Lactate")
            ],
        },
    )


def _test_action_config():
    from ehr2rl.actions import ActionConfig, DoseBins

    return ActionConfig(
        vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3)),
        fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0)),
    )
