"""Build timestep-aligned medication action arrays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ehr2rl.actions.discretize import DoseBins
from ehr2rl.actions.fluids import fluid_amount
from ehr2rl.actions.vasopressors import norepinephrine_equivalent


@dataclass(frozen=True)
class ActionConfig:
    """Configuration for medication-derived action construction."""

    vasopressor_bins: DoseBins
    fluid_bins: DoseBins
    timestep: str = "1h"
    status_include: tuple[str, ...] = ("FinishedRunning", "Changed")


def build_medication_actions(
    inputevents: pd.DataFrame,
    timestamps: np.ndarray,
    *,
    config: ActionConfig,
) -> np.ndarray:
    """Build ``(vasopressor_bin, fluid_bin)`` actions aligned to state timesteps.

    Vasopressor exposure is aggregated with max norepinephrine-equivalent dose
    per timestep so short high-intensity infusion intervals are not diluted.
    Fluid exposure is allocated by overlap duration when an event spans multiple
    timesteps, so one recorded amount is not counted in full more than once.
    """

    bins = _timestamp_bins(timestamps, config.timestep)
    vasopressor_values = np.zeros(len(bins), dtype=float)
    fluid_values = np.zeros(len(bins), dtype=float)

    if inputevents.empty or len(bins) == 0:
        return _stack_actions(vasopressor_values, fluid_values, config)

    events = inputevents.copy()
    if "statusdescription" in events.columns:
        events = events[events["statusdescription"].isin(config.status_include)]
    if events.empty:
        return _stack_actions(vasopressor_values, fluid_values, config)

    events["starttime"] = pd.to_datetime(events["starttime"], errors="raise")
    events["endtime"] = pd.to_datetime(events["endtime"], errors="raise")
    events["nee"] = events.apply(norepinephrine_equivalent, axis=1)
    events["fluid_amount"] = events.apply(fluid_amount, axis=1)

    for row in events.itertuples(index=False):
        start = pd.Timestamp(row.starttime)
        end = pd.Timestamp(row.endtime)
        for index, bin_start in enumerate(bins):
            bin_end = bin_start + pd.to_timedelta(config.timestep)
            if start < bin_end and end > bin_start:
                vasopressor_values[index] = max(vasopressor_values[index], float(row.nee))
                fluid_values[index] += _allocated_fluid_amount(
                    float(row.fluid_amount),
                    start,
                    end,
                    bin_start,
                    bin_end,
                )

    return _stack_actions(vasopressor_values, fluid_values, config)


def _timestamp_bins(timestamps: np.ndarray, timestep: str) -> pd.DatetimeIndex:
    datetime_values = pd.to_datetime(np.asarray(timestamps, dtype=float), unit="s")
    return pd.DatetimeIndex(datetime_values).floor(timestep)


def _stack_actions(
    vasopressor_values: np.ndarray,
    fluid_values: np.ndarray,
    config: ActionConfig,
) -> np.ndarray:
    vasopressor_bins = config.vasopressor_bins.assign(vasopressor_values)
    fluid_bins = config.fluid_bins.assign(fluid_values)
    return np.column_stack([vasopressor_bins, fluid_bins]).astype(int)


def _allocated_fluid_amount(
    amount: float,
    event_start: pd.Timestamp,
    event_end: pd.Timestamp,
    bin_start: pd.Timestamp,
    bin_end: pd.Timestamp,
) -> float:
    duration_seconds = (event_end - event_start).total_seconds()
    if amount <= 0.0 or duration_seconds <= 0.0:
        return 0.0
    overlap_start = max(event_start, bin_start)
    overlap_end = min(event_end, bin_end)
    overlap_seconds = max(0.0, (overlap_end - overlap_start).total_seconds())
    return amount * (overlap_seconds / duration_seconds)
