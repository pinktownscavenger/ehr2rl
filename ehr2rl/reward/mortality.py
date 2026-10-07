"""Mortality-based terminal reward."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import PatientTrajectory
from ehr2rl.reward.base import BaseReward


class MortalityReward(BaseReward):
    """Terminal reward for in-hospital survival.

    Reads ``metadata["died"]``; a missing key counts as survival.

    Parameters
    ----------
    survival_reward
        Reward at the final step for survivors.
    death_penalty
        Reward at the final step for in-hospital deaths.
    """

    def __init__(self, survival_reward: float = 1.0, death_penalty: float = -1.0) -> None:
        self.survival_reward = survival_reward
        self.death_penalty = death_penalty

    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        """Place the survival reward or death penalty at the last terminal step.

        Parameters
        ----------
        trajectory
            Trajectory with at least one ``True`` terminal.

        Returns
        -------
        numpy.ndarray
            Shape ``(T,)``, zero except at the last terminal step.
        """
        rewards = np.zeros(trajectory.n_steps, dtype=float)
        terminal_index = int(np.flatnonzero(trajectory.terminals)[-1])
        rewards[terminal_index] = (
            self.death_penalty
            if bool(trajectory.metadata.get("died", False))
            else self.survival_reward
        )
        return rewards
