"""Export datasets to d3rlpy."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import EHRDataset


def to_d3rlpy(dataset: EHRDataset):
    """Convert an EHRDataset to d3rlpy's MDPDataset."""

    try:
        from d3rlpy.dataset import MDPDataset
    except ImportError as exc:
        raise ImportError(
            "d3rlpy export requires the optional dependency. "
            "Install it with `pip install ehr2rl[d3rlpy]`."
        ) from exc

    observations, actions, rewards, terminals = arrays_for_d3rlpy(dataset)
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

    observations = np.vstack([trajectory.states for trajectory in dataset])
    actions = np.vstack([trajectory.actions for trajectory in dataset])
    rewards = np.concatenate([trajectory.rewards for trajectory in dataset])
    terminals = np.concatenate([trajectory.terminals for trajectory in dataset])
    return observations, actions, rewards, terminals
