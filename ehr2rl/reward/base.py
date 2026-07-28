"""Reward base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ehr2rl.data.dataset import EHRDataset, PatientTrajectory


class BaseReward(ABC):
    """Base class for swappable reward functions."""

    @abstractmethod
    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        """Return one reward value per timestep."""

    def shape(self, dataset: EHRDataset, policy: object | None = None) -> EHRDataset:
        """Return a dataset copy with rewards computed for every trajectory."""

        _ = policy
        return dataset.copy_with(
            trajectory.with_rewards(self.compute(trajectory)) for trajectory in dataset
        )
