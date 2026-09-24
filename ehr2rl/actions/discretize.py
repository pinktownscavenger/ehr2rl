"""Dose discretization helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DoseBins:
    """Assign continuous dose values to integer bins.

    Bin 0 is reserved for exactly zero or lower values. Positive values are
    assigned with ``numpy.searchsorted(..., side="right")`` so edge values fall
    into the higher bin.
    """

    edges: tuple[float, ...]
    labels: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if not self.edges:
            raise ValueError("edges must contain at least one value.")
        if tuple(sorted(self.edges)) != self.edges:
            raise ValueError("edges must be sorted in ascending order.")
        if self.labels is not None and len(self.labels) != len(self.edges) + 1:
            raise ValueError("labels must contain len(edges) + 1 values.")

    def assign(self, values: np.ndarray | pd.Series) -> np.ndarray:
        """Return one bin label per dose value."""

        array = np.asarray(values, dtype=float)
        bins = np.searchsorted(np.asarray(self.edges, dtype=float), array, side="right")
        bins = np.where(array <= 0.0, 0, bins)
        if self.labels is None:
            return bins.astype(int)
        labels = np.asarray(self.labels, dtype=int)
        return labels[bins]
