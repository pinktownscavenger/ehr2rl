import pytest

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


def test_make_synthetic_dataset_is_deterministic():
    first = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=11)
    second = make_synthetic_dataset(n_patients=1, trajectory_length=4, seed=11)

    assert (first[0].states == second[0].states).all()
    assert (first[0].actions == second[0].actions).all()


def test_make_synthetic_dataset_rejects_invalid_sizes():
    with pytest.raises(ValueError, match="n_patients"):
        make_synthetic_dataset(n_patients=0)

    with pytest.raises(ValueError, match="trajectory_length"):
        make_synthetic_dataset(trajectory_length=1)
