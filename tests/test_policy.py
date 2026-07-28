from ehr2rl import BehaviorPolicy, make_synthetic_dataset


def test_behavior_policy_fit_and_propensity_scores():
    ds = make_synthetic_dataset(n_patients=5, trajectory_length=8, seed=5)

    policy = BehaviorPolicy().fit(ds)
    scores = policy.propensity_scores(ds)

    assert scores.shape == (40,)
    assert ((scores >= 0) & (scores <= 1)).all()
