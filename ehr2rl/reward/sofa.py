"""SOFA delta reward."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import PatientTrajectory
from ehr2rl.reward.base import BaseReward


class SofaReward(BaseReward):
    """Reward decreases in SOFA score and penalize increases."""

    def __init__(self, clip: tuple[float, float] | None = (-5.0, 5.0)) -> None:
        self.clip = clip

    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        if "sofa_scores" not in trajectory.metadata:
            raise ValueError("SofaReward requires trajectory.metadata['sofa_scores'].")

        sofa_scores = np.asarray(trajectory.metadata["sofa_scores"], dtype=float)
        if sofa_scores.shape != (trajectory.n_steps,):
            raise ValueError("sofa_scores must have shape (T,).")

        rewards = np.zeros(trajectory.n_steps, dtype=float)
        rewards[1:] = sofa_scores[:-1] - sofa_scores[1:]
        if self.clip is not None:
            rewards = np.clip(rewards, self.clip[0], self.clip[1])
        return rewards
