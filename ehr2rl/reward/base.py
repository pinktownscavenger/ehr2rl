"""Reward base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ehr2rl.data.dataset import EHRDataset, PatientTrajectory


class BaseReward(ABC):
    """Base class for reward functions.

    Subclasses implement `compute`; `shape` applies it to every trajectory in a
    dataset.
    """

    @abstractmethod
    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        """Return one reward per timestep for a trajectory.

        Parameters
        ----------
        trajectory
            Trajectory to score. It must not be modified.

        Returns
        -------
        numpy.ndarray
            Shape ``(T,)``.
        """

    def shape(self, dataset: EHRDataset, policy: object | None = None) -> EHRDataset:
        """Return a copy of a dataset with rewards computed for every trajectory.

        Parameters
        ----------
        dataset
            Input dataset. It is not modified.
        policy
            Reserved for policy-dependent rewards. Ignored by all built-in
            rewards.

        Returns
        -------
        EHRDataset
            A new dataset with new trajectories.
        """

        _ = policy
        return dataset.copy_with(
            trajectory.with_rewards(self.compute(trajectory)) for trajectory in dataset
        )
