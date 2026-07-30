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


def test_mortality_reward_rewards_survival():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=5, seed=12)
    trajectory = ds[0]
    trajectory.metadata["died"] = False

    rewards = MortalityReward().compute(trajectory)

    assert rewards[-1] == 1


def test_reward_shape_returns_dataset_copy_with_rewards():
    ds = make_synthetic_dataset(n_patients=2, trajectory_length=4, seed=13)

    shaped = MortalityReward().shape(ds)

    assert shaped is not ds
    assert len(shaped) == len(ds)
    assert shaped[0].rewards[-1] in {-1, 1}


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


def test_sofa_reward_rejects_wrong_score_shape():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=14)
    ds[0].metadata["sofa_scores"] = np.array([1, 2])

    with pytest.raises(ValueError, match="shape"):
        SofaReward().compute(ds[0])
