from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ehr2rl import EHRDataset, EHRValidationError, PatientTrajectory
from ehr2rl.data.alignment import align_events
from ehr2rl.data.loaders import load_labs, load_vitals


def test_load_admissions_validates_schema(tmp_path: Path):
    path = tmp_path / "admissions.csv"
    pd.DataFrame({"subject_id": [1]}).to_csv(path, index=False)

    with pytest.raises(EHRValidationError, match="missing columns"):
        EHRDataset(tmp_path).load_admissions()


def test_load_missing_table_raises_validation_error(tmp_path: Path):
    with pytest.raises(EHRValidationError, match="does not exist"):
        EHRDataset(tmp_path).load_labs()


def test_load_vitals_rejects_bad_numeric_values(tmp_path: Path):
    path = tmp_path / "chartevents.csv"
    pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "charttime": ["2026-01-01 00:00:00"],
            "itemid": [220045],
            "valuenum": ["not-a-number"],
        }
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="Unable to parse"):
        load_vitals(path)


def test_load_labs_accepts_mimic_demo_header_shape(tmp_path: Path):
    path = tmp_path / "labevents.csv.gz"
    pd.DataFrame(
        {
            "labevent_id": [172061],
            "subject_id": [10014354],
            "hadm_id": [29600294],
            "specimen_id": [1808066],
            "itemid": [51277],
            "order_provider_id": [""],
            "charttime": ["2148-08-16 00:00:00"],
            "storetime": ["2148-08-16 01:30:00"],
            "value": ["15.4"],
            "valuenum": [15.4],
            "valueuom": ["%"],
            "ref_range_lower": [10.5],
            "ref_range_upper": [15.5],
            "flag": [""],
            "priority": ["ROUTINE"],
            "comments": [""],
        }
    ).to_csv(path, index=False, compression="gzip")

    labs = load_labs(path)

    assert labs.loc[0, "itemid"] == 51277
    assert labs.loc[0, "valuenum"] == 15.4


def test_load_vitals_accepts_mimic_demo_chartevents_header(tmp_path: Path):
    path = tmp_path / "chartevents.csv.gz"
    pd.DataFrame(
        {
            "subject_id": [10005817],
            "hadm_id": [20626031],
            "stay_id": [32604416],
            "caregiver_id": [6770],
            "charttime": ["2132-12-16 00:00:00"],
            "storetime": ["2132-12-15 23:45:00"],
            "itemid": [220045],
            "value": ["82"],
            "valuenum": [82],
            "valueuom": ["bpm"],
            "warning": [0],
        }
    ).to_csv(path, index=False, compression="gzip")

    vitals = load_vitals(path)

    assert vitals.loc[0, "itemid"] == 220045
    assert vitals.loc[0, "valuenum"] == 82


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


def test_chainable_load_uses_mimic_iv_default_paths(tmp_path: Path):
    hosp = tmp_path / "hosp"
    icu = tmp_path / "icu"
    hosp.mkdir()
    icu.mkdir()
    pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "admittime": ["2026-01-01 00:00:00"],
            "dischtime": ["2026-01-01 01:00:00"],
            "deathtime": [""],
            "admission_type": ["URGENT"],
            "admit_provider_id": ["P1"],
            "admission_location": ["TRANSFER"],
            "discharge_location": ["HOME"],
            "insurance": ["Other"],
            "language": ["ENGLISH"],
            "marital_status": ["SINGLE"],
            "race": ["UNKNOWN"],
            "edregtime": [""],
            "edouttime": [""],
            "hospital_expire_flag": [0],
        }
    ).to_csv(hosp / "admissions.csv.gz", index=False, compression="gzip")
    pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "stay_id": [20],
            "caregiver_id": [30],
            "charttime": ["2026-01-01 00:15:00"],
            "storetime": ["2026-01-01 00:20:00"],
            "itemid": [220045],
            "value": ["80"],
            "valuenum": [80],
            "valueuom": ["bpm"],
            "warning": [0],
        }
    ).to_csv(icu / "chartevents.csv.gz", index=False, compression="gzip")
    pd.DataFrame(
        {
            "labevent_id": [1],
            "subject_id": [1],
            "hadm_id": [10],
            "specimen_id": [2],
            "itemid": [51277],
            "order_provider_id": [""],
            "charttime": ["2026-01-01 00:30:00"],
            "storetime": ["2026-01-01 01:00:00"],
            "value": ["15"],
            "valuenum": [15],
            "valueuom": ["%"],
            "ref_range_lower": [10],
            "ref_range_upper": [16],
            "flag": [""],
            "priority": ["ROUTINE"],
            "comments": [""],
        }
    ).to_csv(hosp / "labevents.csv.gz", index=False, compression="gzip")

    ds = EHRDataset(tmp_path).load_admissions().load_vitals().load_labs().featurize()

    assert len(ds) == 1
    assert ds[0].states.shape == (2, 2)


def test_align_events_averages_values_in_time_bins():
    events = pd.DataFrame(
        {
            "subject_id": [1, 1],
            "hadm_id": [10, 10],
            "charttime": pd.to_datetime(
                ["2026-01-01 00:05:00", "2026-01-01 00:50:00"]
            ),
            "itemid": [220045, 220045],
            "valuenum": [80.0, 100.0],
        }
    )

    aligned = align_events(events, resample="1h")

    assert aligned.shape[0] == 1
    assert aligned.loc[0, "valuenum"] == 90.0


def test_patient_trajectory_rejects_zero_timesteps():
    with pytest.raises(ValueError, match="at least one timestep"):
        PatientTrajectory(
            subject_id="s",
            admission_id="h",
            timestamps=np.array([]),
            states=np.empty((0, 2)),
            actions=np.empty((0, 1)),
            rewards=np.array([]),
            terminals=np.array([], dtype=bool),
        )


def test_patient_trajectory_reshapes_one_dimensional_actions():
    trajectory = PatientTrajectory(
        subject_id="s",
        admission_id="h",
        timestamps=np.array([1, 2]),
        states=np.ones((2, 2)),
        actions=np.array([0, 1]),
        rewards=np.zeros(2),
        terminals=np.array([False, True]),
    )

    assert trajectory.actions.shape == (2, 1)
