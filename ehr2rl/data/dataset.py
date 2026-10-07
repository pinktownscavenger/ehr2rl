"""Core dataset and trajectory containers."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

from ehr2rl.data.alignment import align_events
from ehr2rl.data.loaders import load_admissions, load_labs, load_vitals


@dataclass
class PatientTrajectory:
    """One patient's episode as aligned per-timestep arrays.

    ``T`` is the number of timesteps, ``D`` the number of state features, and
    ``A`` the number of action columns. Arrays are converted to NumPy and their
    shapes validated on construction; a one-dimensional ``actions`` array is
    reshaped to ``(T, 1)``.

    Parameters
    ----------
    subject_id
        MIMIC-IV ``subject_id``, as a string.
    admission_id
        MIMIC-IV ``hadm_id``, as a string.
    timestamps
        Shape ``(T,)``. Unix time in seconds for each step.
    states
        Shape ``(T, D)``, float. Column names are in
        ``metadata["feature_names"]`` when known.
    actions
        Shape ``(T, A)``.
    rewards
        Shape ``(T,)``, float.
    terminals
        Shape ``(T,)``, bool. ``True`` where the episode ends.
    metadata
        Per-trajectory information such as ``died``, ``feature_names``,
        ``action_names``, ``action_sizes``, ``sofa_scores``, and ``provenance``.

    Raises
    ------
    ValueError
        If there are no timesteps or an array has the wrong shape.
    """

    subject_id: str
    admission_id: str
    timestamps: np.ndarray
    states: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    terminals: np.ndarray
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.timestamps = np.asarray(self.timestamps)
        self.states = np.asarray(self.states, dtype=float)
        self.actions = np.asarray(self.actions)
        self.rewards = np.asarray(self.rewards, dtype=float)
        self.terminals = np.asarray(self.terminals, dtype=bool)
        self._validate_shapes()

    @property
    def n_steps(self) -> int:
        """Number of timesteps ``T``."""
        return int(self.timestamps.shape[0])

    def with_rewards(self, rewards: np.ndarray) -> PatientTrajectory:
        """Return a copy of this trajectory with different rewards.

        Parameters
        ----------
        rewards
            Shape ``(T,)``. Converted to float.

        Returns
        -------
        PatientTrajectory
            A new, validated trajectory. ``metadata`` is shared with this one,
            not copied.
        """
        return replace(self, rewards=np.asarray(rewards, dtype=float))

    def _validate_shapes(self) -> None:
        steps = self.timestamps.shape[0]
        if steps == 0:
            raise ValueError("trajectories must contain at least one timestep.")
        if self.states.ndim != 2:
            raise ValueError("states must have shape (T, D).")
        if self.actions.ndim == 1:
            self.actions = self.actions.reshape(-1, 1)
        if self.actions.ndim != 2:
            raise ValueError("actions must have shape (T, A) or (T,).")
        if self.states.shape[0] != steps:
            raise ValueError("states must have the same T as timestamps.")
        if self.actions.shape[0] != steps:
            raise ValueError("actions must have the same T as timestamps.")
        if self.rewards.shape != (steps,):
            raise ValueError("rewards must have shape (T,).")
        if self.terminals.shape != (steps,):
            raise ValueError("terminals must have shape (T,).")


class EHRDataset:
    """A collection of patient trajectories.

    Supports ``len()``, iteration, and integer indexing over its trajectories.
    The ``load_*`` and ``featurize`` methods implement the frozen local CSV
    path. They modify the dataset in place and return it, so calls can be
    chained.

    Parameters
    ----------
    root
        Directory of MIMIC-IV-style CSV tables. Needed only by the ``load_*``
        methods.
    trajectories
        Initial trajectories.

    Attributes
    ----------
    trajectories
        The trajectories, as a list.
    tables
        Raw tables loaded by the ``load_*`` methods, keyed by name.
    """

    def __init__(
        self,
        root: str | Path | None = None,
        trajectories: Iterable[PatientTrajectory] | None = None,
    ) -> None:
        self.root = Path(root) if root is not None else None
        self.trajectories = list(trajectories or [])
        self.tables: dict[str, pd.DataFrame] = {}

    def __len__(self) -> int:
        return len(self.trajectories)

    def __iter__(self) -> Iterator[PatientTrajectory]:
        return iter(self.trajectories)

    def __getitem__(self, index: int) -> PatientTrajectory:
        return self.trajectories[index]

    def copy_with(self, trajectories: Iterable[PatientTrajectory]) -> EHRDataset:
        """Return a new dataset with this one's root and tables but other trajectories.

        Parameters
        ----------
        trajectories
            Trajectories for the new dataset.

        Returns
        -------
        EHRDataset
            A new dataset. The ``tables`` mapping is copied; the tables
            themselves are shared.
        """
        ds = EHRDataset(root=self.root, trajectories=trajectories)
        ds.tables = dict(self.tables)
        return ds

    def load_admissions(self, filename: str = "hosp/admissions.csv.gz") -> EHRDataset:
        """Load the admissions table from ``root``.

        Parameters
        ----------
        filename
            Path relative to ``root``. If it does not exist, ``admissions.csv``
            is tried instead.

        Returns
        -------
        EHRDataset
            This dataset, for chaining.

        Raises
        ------
        EHRValidationError
            If the file is missing or lacks required columns.
        ValueError
            If ``root`` is not set.
        """
        self.tables["admissions"] = load_admissions(
            self._table_path(filename, fallback="admissions.csv")
        )
        return self

    def load_vitals(
        self, filename: str = "icu/chartevents.csv.gz", resample: str = "1h"
    ) -> EHRDataset:
        """Load ICU chart events from ``root`` and average them into time bins.

        Parameters
        ----------
        filename
            Path relative to ``root``. If it does not exist, ``vitals.csv`` is
            tried instead.
        resample
            Bin width as a pandas frequency string.

        Returns
        -------
        EHRDataset
            This dataset, for chaining.

        Raises
        ------
        EHRValidationError
            If the file is missing or lacks required columns.
        ValueError
            If ``root`` is not set or a value is not numeric.
        """
        self.tables["vitals"] = load_vitals(
            self._table_path(filename, fallback="vitals.csv")
        )
        self.tables["vitals_aligned"] = align_events(self.tables["vitals"], resample)
        return self

    def load_labs(
        self, filename: str = "hosp/labevents.csv.gz", codes: list[str] | None = None
    ) -> EHRDataset:
        """Load lab events from ``root``.

        Parameters
        ----------
        filename
            Path relative to ``root``. If it does not exist, ``labs.csv`` is
            tried instead.
        codes
            Lab itemids to keep. All rows are kept when ``None``.

        Returns
        -------
        EHRDataset
            This dataset, for chaining.

        Raises
        ------
        EHRValidationError
            If the file is missing or lacks required columns.
        ValueError
            If ``root`` is not set or a value is not numeric.
        """
        labs = load_labs(self._table_path(filename, fallback="labs.csv"))
        if codes is not None:
            labs = labs[labs["itemid"].astype(str).isin({str(code) for code in codes})]
        self.tables["labs"] = labs
        return self

    def featurize(self, pipeline: str = "standard") -> EHRDataset:
        """Build trajectories from the loaded tables, replacing ``trajectories``.

        Does nothing when no tables are loaded.

        Parameters
        ----------
        pipeline
            Featurization pipeline. ``"standard"`` is the only one.

        Returns
        -------
        EHRDataset
            This dataset, for chaining.

        Raises
        ------
        ValueError
            If ``pipeline`` is not ``"standard"``.
        """
        from ehr2rl.data.featurize import build_state_matrix

        if pipeline != "standard":
            raise ValueError("Only the 'standard' featurization pipeline exists in v0.1.")
        if not self.tables:
            return self
        self.trajectories = build_state_matrix(self.tables)
        return self

    def _table_path(self, filename: str, fallback: str | None = None) -> Path:
        if self.root is None:
            raise ValueError("EHRDataset.root is required to load CSV tables.")
        path = self.root / filename
        if path.exists() or fallback is None:
            return path
        fallback_path = self.root / fallback
        return fallback_path if fallback_path.exists() else path
