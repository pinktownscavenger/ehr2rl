import numpy as np
import pandas as pd


def test_build_medication_actions_aligns_to_state_timestamps():
    from ehr2rl.actions import ActionConfig, DoseBins, build_medication_actions

    timestamps = np.array(
        [
            pd.Timestamp("2026-01-01 00:00:00").timestamp(),
            pd.Timestamp("2026-01-01 01:00:00").timestamp(),
        ]
    )
    events = pd.DataFrame(
        {
            "subject_id": [1],
            "hadm_id": [10],
            "starttime": pd.to_datetime(["2026-01-01 00:10:00"]),
            "endtime": pd.to_datetime(["2026-01-01 00:50:00"]),
            "itemid": [221906],
            "rate": [0.2],
            "amount": [0.0],
            "statusdescription": ["FinishedRunning"],
        }
    )
    config = ActionConfig(
        vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3)),
        fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0)),
    )

    actions = build_medication_actions(events, timestamps, config=config)

    assert actions.shape == (2, 2)
    assert actions[:, 0].tolist() == [2, 0]


def test_paused_inputevent_does_not_create_dose():
    from ehr2rl.actions import ActionConfig, DoseBins, build_medication_actions

    timestamps = np.array([pd.Timestamp("2026-01-01 00:00:00").timestamp()])
    events = pd.DataFrame(
        {
            "starttime": pd.to_datetime(["2026-01-01 00:00:00"]),
            "endtime": pd.to_datetime(["2026-01-01 00:30:00"]),
            "itemid": [221906],
            "rate": [0.5],
            "amount": [0.0],
            "statusdescription": ["Paused"],
        }
    )
    config = ActionConfig(
        vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3)),
        fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0)),
    )

    assert build_medication_actions(events, timestamps, config=config).tolist() == [[0, 0]]


def test_fluid_amount_maps_to_fluid_bin():
    from ehr2rl.actions import ActionConfig, DoseBins, build_medication_actions

    timestamps = np.array([pd.Timestamp("2026-01-01 00:00:00").timestamp()])
    events = pd.DataFrame(
        {
            "starttime": pd.to_datetime(["2026-01-01 00:00:00"]),
            "endtime": pd.to_datetime(["2026-01-01 00:45:00"]),
            "itemid": [225158],
            "rate": [0.0],
            "amount": [750.0],
            "statusdescription": ["FinishedRunning"],
        }
    )
    config = ActionConfig(
        vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3)),
        fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0)),
    )

    assert build_medication_actions(events, timestamps, config=config).tolist() == [[0, 3]]


def test_fluid_amount_is_allocated_by_overlap_duration():
    from ehr2rl.actions import ActionConfig, DoseBins, build_medication_actions

    timestamps = np.array(
        [
            pd.Timestamp("2026-01-01 00:00:00").timestamp(),
            pd.Timestamp("2026-01-01 01:00:00").timestamp(),
        ]
    )
    events = pd.DataFrame(
        {
            "starttime": pd.to_datetime(["2026-01-01 00:30:00"]),
            "endtime": pd.to_datetime(["2026-01-01 01:30:00"]),
            "itemid": [225158],
            "rate": [0.0],
            "amount": [1000.0],
            "statusdescription": ["FinishedRunning"],
        }
    )
    config = ActionConfig(
        vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3)),
        fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0, 750.0)),
    )

    assert build_medication_actions(events, timestamps, config=config).tolist() == [
        [0, 3],
        [0, 3],
    ]
