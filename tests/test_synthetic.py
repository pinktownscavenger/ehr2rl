from ehr2rl import make_synthetic_dataset


def test_make_synthetic_dataset_shapes():
    ds = make_synthetic_dataset(n_patients=3, trajectory_length=12, seed=1)

    assert len(ds) == 3
    for trajectory in ds:
        assert trajectory.states.shape == (12, 4)
        assert trajectory.actions.shape == (12, 1)
        assert trajectory.rewards.shape == (12,)
        assert trajectory.terminals.tolist().count(True) == 1
        assert trajectory.terminals[-1]
        assert trajectory.metadata["sofa_scores"].shape == (12,)
