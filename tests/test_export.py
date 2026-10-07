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
    assert observations.dtype.name == "float32"
    assert rewards.dtype.name == "float32"
    assert terminals.dtype.name == "float32"
    assert terminals.sum() == 2


def test_arrays_for_d3rlpy_rejects_empty_dataset():
    from ehr2rl import EHRDataset

    with pytest.raises(ValueError, match="empty"):
        arrays_for_d3rlpy(EHRDataset())


def test_to_d3rlpy_has_clear_missing_extra_message():
    ds = make_synthetic_dataset(n_patients=1, trajectory_length=3, seed=7)

    try:
        import d3rlpy  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="ehr2rl\\[d3rlpy\\]"):
            to_d3rlpy(ds)


def test_to_d3rlpy_builds_dataset_when_extra_is_installed():
    pytest.importorskip("d3rlpy")
    ds = make_synthetic_dataset(n_patients=2, trajectory_length=6, seed=8)
    ds = MortalityReward().shape(ds)

    mdp_dataset = to_d3rlpy(ds)

    assert type(mdp_dataset).__name__ == "MDPDataset"


def test_to_d3rlpy_writes_sidecar_when_metadata_present(tmp_path):
    pytest.importorskip("d3rlpy")
    ds = MortalityReward().shape(
        make_synthetic_dataset(n_patients=1, trajectory_length=3, seed=1)
    )
    for trajectory in ds:
        trajectory.metadata["provenance"] = {
            "bigquery_job_ids": ["job_1"],
            "query_hash": "abc",
            "itemid_map_version": "v3_1",
            "feature_preset": "vitals_only",
            "extraction_timestamp": "2026-09-24T00:00:00Z",
            "mimic_version": "3.1",
        }

    to_d3rlpy(ds, provenance_path=tmp_path / "sidecar.json")

    assert (tmp_path / "sidecar.json").exists()


def test_arrays_for_d3rlpy_encodes_multi_column_actions_as_joint_index():
    import numpy as np

    ds = MortalityReward().shape(
        make_synthetic_dataset(
            n_patients=3, trajectory_length=5, seed=2, include_medication_metadata=True
        )
    )
    raw = np.vstack([t.actions for t in ds])

    _, actions, _, _ = arrays_for_d3rlpy(ds)

    assert actions.shape == (15, 1)
    assert actions[:, 0].tolist() == (raw[:, 0] * 2 + raw[:, 1]).tolist()


def test_arrays_for_d3rlpy_rejects_multi_column_integer_actions_without_sizes():
    ds = make_synthetic_dataset(
        n_patients=1, trajectory_length=3, include_medication_metadata=True
    )
    del ds[0].metadata["action_sizes"]

    with pytest.raises(ValueError, match="action_sizes"):
        arrays_for_d3rlpy(ds)


def test_arrays_for_d3rlpy_rejects_actions_outside_declared_sizes():
    ds = make_synthetic_dataset(
        n_patients=1, trajectory_length=3, include_medication_metadata=True
    )
    ds[0].actions[0, 1] = 5

    with pytest.raises(ValueError, match="outside"):
        arrays_for_d3rlpy(ds)


def test_arrays_for_d3rlpy_rejects_mismatched_action_sizes():
    ds = make_synthetic_dataset(
        n_patients=2, trajectory_length=3, include_medication_metadata=True
    )
    ds[1].metadata["action_sizes"] = [3, 2]

    with pytest.raises(ValueError, match="same action_sizes"):
        arrays_for_d3rlpy(ds)


def test_arrays_for_d3rlpy_passes_continuous_actions_through():
    import numpy as np

    ds = make_synthetic_dataset(n_patients=2, trajectory_length=3)
    for trajectory in ds:
        trajectory.actions = np.full((3, 2), 0.25)

    _, actions, _, _ = arrays_for_d3rlpy(ds)

    assert actions.shape == (6, 2)
    assert actions.dtype.kind == "f"


def test_to_d3rlpy_declares_full_joint_action_space_and_trains_discrete_algorithm():
    d3rlpy = pytest.importorskip("d3rlpy")
    from d3rlpy.constants import ActionSpace

    ds = MortalityReward().shape(
        make_synthetic_dataset(
            n_patients=4, trajectory_length=6, seed=3, include_medication_metadata=True
        )
    )

    mdp_dataset = to_d3rlpy(ds)

    assert mdp_dataset.dataset_info.action_space == ActionSpace.DISCRETE
    assert mdp_dataset.dataset_info.action_size == 4
    algorithm = d3rlpy.algos.DiscreteCQLConfig(batch_size=4).create(device=False)
    algorithm.fit(
        mdp_dataset,
        n_steps=1,
        n_steps_per_epoch=1,
        logger_adapter=d3rlpy.logging.NoopAdapterFactory(),
        show_progress=False,
    )


def test_replaced_actions_error_explains_how_to_update_action_sizes():
    import numpy as np

    ds = make_synthetic_dataset(n_patients=1, trajectory_length=3)
    ds[0].actions = np.array([[0], [1], [2]])

    with pytest.raises(ValueError, match=r"update metadata\['action_sizes'\]"):
        arrays_for_d3rlpy(ds)


def test_column_count_mismatch_error_explains_how_to_update_action_sizes():
    import numpy as np

    ds = make_synthetic_dataset(
        n_patients=1, trajectory_length=3, include_medication_metadata=True
    )
    sizes = ds[0].metadata["action_sizes"]
    ds[0].actions = np.ravel_multi_index(tuple(ds[0].actions.T), sizes).reshape(-1, 1)

    with pytest.raises(ValueError, match=r"update metadata\['action_sizes'\]"):
        arrays_for_d3rlpy(ds)
