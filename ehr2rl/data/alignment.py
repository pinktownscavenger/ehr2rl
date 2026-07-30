"""Simple time alignment helpers."""

from __future__ import annotations

import pandas as pd


def align_events(events: pd.DataFrame, resample: str = "1h") -> pd.DataFrame:
    """Aggregate event rows onto regular time bins per admission and item."""

    if events.empty:
        return events.copy()

    df = events.copy()
    df["time_bin"] = df["charttime"].dt.floor(resample)
    grouped = (
        df.groupby(["subject_id", "hadm_id", "time_bin", "itemid"], as_index=False)[
            "valuenum"
        ]
        .mean()
        .sort_values(["subject_id", "hadm_id", "time_bin", "itemid"])
    )
    return grouped
