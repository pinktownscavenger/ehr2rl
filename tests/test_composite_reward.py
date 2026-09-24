import numpy as np
import pytest


def test_composite_reward_applies_weights():
    from ehr2rl import (
        CompositeReward,
        MortalityReward,
        SofaReward,
        make_synthetic_dataset,
    )

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=1)
    ds[0].metadata["died"] = False
    ds[0].metadata["sofa_scores"] = np.array([4, 3, 3, 2])

    rewards = CompositeReward(
        [(MortalityReward(), 2.0), (SofaReward(clip=None), 0.5)]
    ).compute(ds[0])

    assert rewards.tolist() == [0.0, 0.5, 0.0, 2.5]


def test_composite_reward_requires_base_reward_components():
    from ehr2rl import CompositeReward

    with pytest.raises(TypeError, match="BaseReward"):
        CompositeReward([(object(), 1.0)])


def test_composite_reward_rejects_wrong_shape():
    from ehr2rl import CompositeReward, make_synthetic_dataset
    from ehr2rl.reward.base import BaseReward

    class BadReward(BaseReward):
        def compute(self, trajectory):
            return np.array([1.0])

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=1)

    with pytest.raises(ValueError, match="shape"):
        CompositeReward([(BadReward(), 1.0)]).compute(ds[0])
