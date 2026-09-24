import numpy as np
import pytest


def test_readmission_reward_penalizes_terminal_readmission():
    from ehr2rl import ReadmissionReward, make_synthetic_dataset

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=1)
    ds[0].metadata["readmitted_within_30_days"] = True
    ds[0].metadata["died"] = False

    rewards = ReadmissionReward().compute(ds[0])

    assert rewards[:-1].tolist() == [0.0, 0.0, 0.0]
    assert rewards[-1] == -1.0


def test_readmission_reward_death_does_not_count_as_readmission():
    from ehr2rl import ReadmissionReward, make_synthetic_dataset

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=1)
    ds[0].metadata["readmitted_within_30_days"] = True
    ds[0].metadata["died"] = True

    rewards = ReadmissionReward().compute(ds[0])

    assert rewards[-1] == 0.0


def test_readmission_reward_masks_censored_admission():
    from ehr2rl import ReadmissionReward, make_synthetic_dataset

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=1)
    ds[0].metadata["readmitted_within_30_days"] = None
    ds[0].metadata["died"] = False

    rewards = ReadmissionReward().compute(ds[0])

    assert np.isnan(rewards[-1])


def test_readmission_reward_requires_readmission_metadata():
    from ehr2rl import ReadmissionReward, make_synthetic_dataset

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=1)

    with pytest.raises(ValueError, match="readmitted_within_30_days"):
        ReadmissionReward().compute(ds[0])
