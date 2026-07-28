import numpy as np
import pytest

from ehr2rl import MortalityReward, SofaReward, make_synthetic_dataset


def test_mortality_reward_is_terminal_only():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=5, seed=2)
    trajectory = ds[0]
    trajectory.metadata["died"] = True

    rewards = MortalityReward().compute(trajectory)

    assert rewards[:-1].tolist() == [0, 0, 0, 0]
    assert rewards[-1] == -1


def test_sofa_reward_uses_score_improvement():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=3)
    trajectory = ds[0]
    trajectory.metadata["sofa_scores"] = np.array([8, 7, 9, 6])

    rewards = SofaReward(clip=None).compute(trajectory)

    assert rewards.tolist() == [0, 1, -2, 3]


def test_sofa_reward_requires_metadata():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=4)
    ds[0].metadata.pop("sofa_scores")

    with pytest.raises(ValueError, match="sofa_scores"):
        SofaReward().compute(ds[0])
