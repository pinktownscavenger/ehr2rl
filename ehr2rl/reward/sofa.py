"""SOFA delta reward."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import PatientTrajectory
from ehr2rl.reward.base import BaseReward


class SofaReward(BaseReward):
    """Dense reward for change in SOFA score; improvement is positive.

    Parameters
    ----------
    clip
        ``(low, high)`` bounds for each step's reward, or ``None`` for no
        clipping.
    """

    def __init__(self, clip: tuple[float, float] | None = (-5.0, 5.0)) -> None:
        self.clip = clip

    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        """Return ``sofa[t - 1] - sofa[t]`` per step, with ``0`` at the first step.

        Parameters
        ----------
        trajectory
            Trajectory with ``metadata["sofa_scores"]`` of shape ``(T,)``.

        Returns
        -------
        numpy.ndarray
            Shape ``(T,)``, clipped to ``clip``.

        Raises
        ------
        ValueError
            If ``sofa_scores`` is missing or has the wrong shape.
        """
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
