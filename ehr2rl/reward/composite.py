"""Composite reward functions."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ehr2rl.data.dataset import PatientTrajectory
from ehr2rl.reward.base import BaseReward


class CompositeReward(BaseReward):
    """Weighted sum of other reward functions.

    Parameters
    ----------
    components
        ``(reward, weight)`` pairs. At least one is required.

    Raises
    ------
    ValueError
        If ``components`` is empty.
    TypeError
        If a component is not a `~ehr2rl.reward.BaseReward`.
    """

    def __init__(self, components: Sequence[tuple[BaseReward, float]]) -> None:
        if not components:
            raise ValueError("CompositeReward requires at least one component.")
        normalized = []
        for reward, weight in components:
            if not isinstance(reward, BaseReward):
                raise TypeError("CompositeReward components must be BaseReward instances.")
            normalized.append((reward, float(weight)))
        self.components = tuple(normalized)

    def compute(self, trajectory: PatientTrajectory) -> np.ndarray:
        """Return the weighted sum of every component's rewards.

        Parameters
        ----------
        trajectory
            Trajectory with whatever metadata the components need.

        Returns
        -------
        numpy.ndarray
            Shape ``(T,)``.

        Raises
        ------
        ValueError
            If a component returns the wrong shape.
        """
        total = np.zeros(trajectory.n_steps, dtype=float)
        expected_shape = (trajectory.n_steps,)
        for reward, weight in self.components:
            values = np.asarray(reward.compute(trajectory), dtype=float)
            if values.shape != expected_shape:
                raise ValueError(
                    f"{type(reward).__name__} returned shape {values.shape}, "
                    f"expected {expected_shape}."
                )
            total += values * weight
        return total
