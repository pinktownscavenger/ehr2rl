"""Mortality-based terminal reward."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import PatientTrajectory
from ehr2rl.reward.base import BaseReward


class MortalityReward(BaseReward):
    """Reward survival at terminal time and penalize in-hospital death."""

    def __init__(self, survival_reward: float = 1.0, death_penalty: float = -1.0) -> None:
        self.survival_reward = survival_reward
        self.death_penalty = death_penalty

    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        rewards = np.zeros(trajectory.n_steps, dtype=float)
        terminal_index = int(np.flatnonzero(trajectory.terminals)[-1])
        rewards[terminal_index] = (
            self.death_penalty
            if bool(trajectory.metadata.get("died", False))
            else self.survival_reward
        )
        return rewards
