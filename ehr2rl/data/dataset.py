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
    """One time-indexed patient episode."""

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
        return int(self.timestamps.shape[0])

    def with_rewards(self, rewards: np.ndarray) -> PatientTrajectory:
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
    """Collection of patient trajectories with a chainable preprocessing API."""

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
        ds = EHRDataset(root=self.root, trajectories=trajectories)
        ds.tables = dict(self.tables)
        return ds

    def load_admissions(self, filename: str = "hosp/admissions.csv.gz") -> EHRDataset:
        self.tables["admissions"] = load_admissions(
            self._table_path(filename, fallback="admissions.csv")
        )
        return self

    def load_vitals(
        self, filename: str = "icu/chartevents.csv.gz", resample: str = "1h"
    ) -> EHRDataset:
        self.tables["vitals"] = load_vitals(
            self._table_path(filename, fallback="vitals.csv")
        )
        self.tables["vitals_aligned"] = align_events(self.tables["vitals"], resample)
        return self

    def load_labs(
        self, filename: str = "hosp/labevents.csv.gz", codes: list[str] | None = None
    ) -> EHRDataset:
        labs = load_labs(self._table_path(filename, fallback="labs.csv"))
        if codes is not None:
            labs = labs[labs["itemid"].astype(str).isin({str(code) for code in codes})]
        self.tables["labs"] = labs
        return self

    def featurize(self, pipeline: str = "standard") -> EHRDataset:
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
