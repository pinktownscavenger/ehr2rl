"""Readmission-based terminal reward."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import PatientTrajectory
from ehr2rl.reward.base import BaseReward


class ReadmissionReward(BaseReward):
    """Terminal reward based on 30-day readmission metadata."""

    def __init__(
        self,
        window_days: int = 30,
        readmitted_reward: float = -1.0,
        not_readmitted_reward: float = 1.0,
        censored_value: float = np.nan,
    ) -> None:
        self.window_days = window_days
        self.readmitted_reward = readmitted_reward
        self.not_readmitted_reward = not_readmitted_reward
        self.censored_value = censored_value

    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        if "readmitted_within_30_days" not in trajectory.metadata:
            raise ValueError("ReadmissionReward requires readmitted_within_30_days.")

        rewards = np.zeros(trajectory.n_steps, dtype=float)
        readmitted = trajectory.metadata["readmitted_within_30_days"]
        died = bool(trajectory.metadata.get("died", False))
        if died:
            rewards[-1] = 0.0
        elif readmitted is None:
            rewards[-1] = self.censored_value
        elif bool(readmitted):
            rewards[-1] = self.readmitted_reward
        else:
            rewards[-1] = self.not_readmitted_reward
        return rewards
