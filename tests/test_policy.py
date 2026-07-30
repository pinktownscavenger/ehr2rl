import numpy as np
import pytest

from ehr2rl import BehaviorPolicy, make_synthetic_dataset


def test_behavior_policy_fit_and_propensity_scores():
    ds = make_synthetic_dataset(n_patients=5, trajectory_length=8, seed=5)

    policy = BehaviorPolicy().fit(ds)
    scores = policy.propensity_scores(ds)

    assert scores.shape == (40,)
    assert ((scores >= 0) & (scores <= 1)).all()


def test_behavior_policy_rejects_empty_dataset():
    from ehr2rl import EHRDataset

    with pytest.raises(ValueError, match="at least one trajectory"):
        BehaviorPolicy().fit(EHRDataset())


def test_behavior_policy_requires_fit_before_prediction():
    policy = BehaviorPolicy()

    with pytest.raises(ValueError, match="must be fit"):
        policy.predict_proba(np.ones((2, 4)))


def test_behavior_policy_handles_single_action_class():
    ds = make_synthetic_dataset(n_patients=2, trajectory_length=4, seed=9)
    for trajectory in ds:
        trajectory.actions[:] = 0

    policy = BehaviorPolicy().fit(ds)
    scores = policy.propensity_scores(ds)

    assert np.allclose(scores, 1.0)


def test_behavior_policy_discretizes_continuous_actions():
    ds = make_synthetic_dataset(n_patients=3, trajectory_length=5, seed=10)
    for index, trajectory in enumerate(ds):
        trajectory.actions = (
            np.linspace(0.1, 0.9, trajectory.n_steps).reshape(-1, 1) + index
        )

    policy = BehaviorPolicy(n_action_bins=3).fit(ds)
    scores = policy.propensity_scores(ds)

    assert policy.discretizer is not None
    assert scores.shape == (15,)
