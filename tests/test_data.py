from pathlib import Path

import pandas as pd
import pytest

from ehr2rl import EHRDataset, EHRValidationError


def test_load_admissions_validates_schema(tmp_path: Path):
    path = tmp_path / "admissions.csv"
    pd.DataFrame({"subject_id": [1]}).to_csv(path, index=False)

    with pytest.raises(EHRValidationError, match="missing columns"):
        EHRDataset(tmp_path).load_admissions()


def test_chainable_load_and_featurize(tmp_path: Path):
    pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "admittime": ["2026-01-01 00:00:00"],
            "dischtime": ["2026-01-01 03:00:00"],
            "hospital_expire_flag": [0],
        }
    ).to_csv(tmp_path / "admissions.csv", index=False)
    pd.DataFrame(
        {
            "subject_id": [1, 1],
            "hadm_id": [10, 10],
            "charttime": ["2026-01-01 00:15:00", "2026-01-01 01:20:00"],
            "itemid": ["heart_rate", "heart_rate"],
            "valuenum": [80, 82],
        }
    ).to_csv(tmp_path / "vitals.csv", index=False)
    pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "charttime": ["2026-01-01 00:30:00"],
            "itemid": ["lactate"],
            "valuenum": [1.2],
        }
    ).to_csv(tmp_path / "labs.csv", index=False)

    ds = (
        EHRDataset(tmp_path)
        .load_admissions()
        .load_vitals(resample="1h")
        .load_labs()
        .featurize()
    )

    assert len(ds) == 1
    assert ds[0].states.shape[1] == 2
    assert ds[0].terminals[-1]
