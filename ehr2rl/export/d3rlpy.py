"""Export datasets to d3rlpy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ehr2rl.data.dataset import EHRDataset
from ehr2rl.provenance import provenance_from_mapping, write_provenance


def to_d3rlpy(dataset: EHRDataset, provenance_path: str | Path | None = None):
    """Convert an EHRDataset to d3rlpy's MDPDataset."""

    try:
        from d3rlpy.dataset import MDPDataset
    except ImportError as exc:
        raise ImportError(
            "d3rlpy export requires the optional dependency. "
            "Install it with `pip install ehr2rl[d3rlpy]`."
        ) from exc

    observations, actions, rewards, terminals = arrays_for_d3rlpy(dataset)
    if provenance_path is not None:
        write_provenance(provenance_path, _dataset_provenance(dataset))
    return MDPDataset(
        observations=observations,
        actions=actions,
        rewards=rewards,
        terminals=terminals,
    )


def arrays_for_d3rlpy(
    dataset: EHRDataset,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return concatenated arrays used by d3rlpy; exposed for lightweight tests."""

    if len(dataset) == 0:
        raise ValueError("Cannot export an empty EHRDataset.")

    observations = np.vstack([trajectory.states for trajectory in dataset]).astype(
        np.float32
    )
    actions = np.vstack([trajectory.actions for trajectory in dataset])
    rewards = np.concatenate([trajectory.rewards for trajectory in dataset]).astype(
        np.float32
    )
    terminals = np.concatenate([trajectory.terminals for trajectory in dataset]).astype(
        np.float32
    )
    return observations, actions, rewards, terminals


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
