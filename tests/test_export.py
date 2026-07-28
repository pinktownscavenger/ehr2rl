import pytest

from ehr2rl import MortalityReward, make_synthetic_dataset, to_d3rlpy
from ehr2rl.export.d3rlpy import arrays_for_d3rlpy


def test_arrays_for_d3rlpy_concatenates_episodes():
    ds = make_synthetic_dataset(n_patients=2, trajectory_length=6, seed=6)
    ds = MortalityReward().shape(ds)

    observations, actions, rewards, terminals = arrays_for_d3rlpy(ds)

    assert observations.shape == (12, 4)
    assert actions.shape == (12, 1)
    assert rewards.shape == (12,)
    assert terminals.shape == (12,)
    assert terminals.sum() == 2


def test_to_d3rlpy_has_clear_missing_extra_message():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=3, seed=7)

    try:
        import d3rlpy  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="ehr2rl\\[d3rlpy\\]"):
            to_d3rlpy(ds)
