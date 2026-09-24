import pytest


def test_provenance_round_trip(tmp_path):
    from ehr2rl.provenance import (
        DatasetProvenance,
        read_provenance,
        write_provenance,
    )

    provenance = DatasetProvenance(
        bigquery_job_ids=("job_1",),
        query_hash="abc",
        itemid_map_version="v3_1",
        feature_preset="sepsis3_core",
        extraction_timestamp="2026-09-24T00:00:00Z",
        mimic_version="3.1",
    )

    path = tmp_path / "dataset.provenance.json"
    write_provenance(path, provenance)

    assert read_provenance(path) == provenance


def test_read_provenance_rejects_missing_fields(tmp_path):
    from ehr2rl.provenance import read_provenance

    path = tmp_path / "bad.json"
    path.write_text('{"query_hash": "abc"}', encoding="utf-8")

    with pytest.raises(ValueError, match="missing"):
        read_provenance(path)
