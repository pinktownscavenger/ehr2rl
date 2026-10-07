"""Export datasets to d3rlpy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ehr2rl.data.dataset import EHRDataset
from ehr2rl.provenance import provenance_from_mapping, write_provenance


def to_d3rlpy(dataset: EHRDataset, provenance_path: str | Path | None = None):
    """Convert an EHRDataset to d3rlpy's MDPDataset.

    Integer actions whose trajectories declare ``metadata["action_sizes"]`` are
    exported as one discrete action with the full declared action space, so
    actions that never occur in the data are still part of it. Several action
    columns are combined into one joint index in row-major order; recover the
    per-column bins with ``numpy.unravel_index(action, action_sizes)``.
    Floating-point actions are exported unchanged as continuous actions.

    Parameters
    ----------
    dataset
        Non-empty dataset with rewards already shaped.
    provenance_path
        Where to write a JSON provenance sidecar. Every trajectory must carry
        the same ``metadata["provenance"]``.

    Returns
    -------
    d3rlpy.dataset.MDPDataset
        One episode per trajectory.

    Raises
    ------
    ImportError
        If the ``d3rlpy`` extra is not installed.
    ValueError
        If the dataset is empty, multi-column integer actions lack
        ``action_sizes``, sizes differ between trajectories, or an action is
        outside its declared size.
    TypeError
        If ``provenance_path`` is given and a trajectory has no provenance.
    """

    try:
        from d3rlpy.constants import ActionSpace
        from d3rlpy.dataset import MDPDataset
    except ImportError as exc:
        raise ImportError(
            "d3rlpy export requires the optional dependency. "
            "Install it with `pip install ehr2rl[d3rlpy]`."
        ) from exc

    observations, actions, rewards, terminals, action_size = _export_arrays(dataset)
    if provenance_path is not None:
        write_provenance(provenance_path, _dataset_provenance(dataset))
    if action_size is None:
        return MDPDataset(
            observations=observations,
            actions=actions,
            rewards=rewards,
            terminals=terminals,
        )
    return MDPDataset(
        observations=observations,
        actions=actions,
        rewards=rewards,
        terminals=terminals,
        action_space=ActionSpace.DISCRETE,
        action_size=action_size,
    )


def arrays_for_d3rlpy(
    dataset: EHRDataset,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return concatenated arrays used by d3rlpy; exposed for lightweight tests."""

    observations, actions, rewards, terminals, _ = _export_arrays(dataset)
    return observations, actions, rewards, terminals


def _export_arrays(
    dataset: EHRDataset,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int | None]:
    if len(dataset) == 0:
        raise ValueError("Cannot export an empty EHRDataset.")

    observations = np.vstack([trajectory.states for trajectory in dataset]).astype(
        np.float32
    )
    actions, action_size = _encode_actions(dataset)
    rewards = np.concatenate([trajectory.rewards for trajectory in dataset]).astype(
        np.float32
    )
    terminals = np.concatenate([trajectory.terminals for trajectory in dataset]).astype(
        np.float32
    )
    return observations, actions, rewards, terminals, action_size


_REPLACED_ACTIONS_HINT = (
    "If you replaced trajectory actions, update metadata['action_sizes'] on every "
    "trajectory to match them."
)


def _encode_actions(dataset: EHRDataset) -> tuple[np.ndarray, int | None]:
    actions = np.vstack([trajectory.actions for trajectory in dataset])
    if not np.issubdtype(actions.dtype, np.integer):
        return actions, None

    declared = [trajectory.metadata.get("action_sizes") for trajectory in dataset]
    if all(sizes is None for sizes in declared):
        if actions.shape[1] > 1:
            raise ValueError(
                "Multi-column integer actions need metadata['action_sizes'] on every "
                "trajectory so they can be exported as one discrete action."
            )
        return actions, None

    first = declared[0]
    if first is None or any(list(other or []) != list(first) for other in declared):
        raise ValueError("All trajectories must declare the same action_sizes.")
    sizes = tuple(int(size) for size in first)
    if len(sizes) != actions.shape[1]:
        raise ValueError(
            f"action_sizes {list(sizes)} does not match {actions.shape[1]} action "
            f"columns. {_REPLACED_ACTIONS_HINT}"
        )
    for column, size in enumerate(sizes):
        values = actions[:, column]
        if values.min() < 0 or values.max() >= size:
            raise ValueError(
                f"Action column {column} has values outside 0..{size - 1} "
                f"declared by action_sizes. {_REPLACED_ACTIONS_HINT}"
            )

    joint = np.ravel_multi_index(tuple(actions.T), sizes)
    return joint.reshape(-1, 1).astype(np.int64), int(np.prod(sizes))


def _dataset_provenance(dataset: EHRDataset):
    provenances: list[dict[str, Any]] = []
    for trajectory in dataset:
        provenance = trajectory.metadata.get("provenance")
        if not isinstance(provenance, dict):
            raise TypeError("All trajectories must include provenance metadata.")
        provenances.append(provenance)

    first = provenance_from_mapping(provenances[0])
    for provenance in provenances[1:]:
        if provenance_from_mapping(provenance) != first:
            raise ValueError("All trajectories must have matching provenance metadata.")
    return first
