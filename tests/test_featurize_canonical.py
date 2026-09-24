import pandas as pd
import pytest


def test_build_state_matrix_preserves_canonical_feature_names():
    from ehr2rl.data.featurize import build_state_matrix

    admissions = pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "admittime": pd.to_datetime(["2026-01-01 00:00:00"]),
            "dischtime": pd.to_datetime(["2026-01-01 02:00:00"]),
            "hospital_expire_flag": [0],
        }
    )
    features = pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "charttime": pd.to_datetime(["2026-01-01 00:00:00"]),
            "feature": ["heart_rate"],
            "valuenum": [80.0],
        }
    )

    trajectories = build_state_matrix({"admissions": admissions, "features": features})

    assert trajectories[0].metadata["feature_names"] == ["heart_rate"]
    assert trajectories[0].states.shape == (1, 1)


def test_build_state_matrix_rejects_incomplete_feature_table():
    from ehr2rl.data.featurize import build_state_matrix

    admissions = pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "admittime": pd.to_datetime(["2026-01-01 00:00:00"]),
            "dischtime": pd.to_datetime(["2026-01-01 02:00:00"]),
            "hospital_expire_flag": [0],
        }
    )
    features = pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "charttime": pd.to_datetime(["2026-01-01 00:00:00"]),
            "valuenum": [80.0],
        }
    )

    with pytest.raises(ValueError, match="feature"):
        build_state_matrix({"admissions": admissions, "features": features})
