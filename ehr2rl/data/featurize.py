"""Feature construction from aligned tables."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ehr2rl.data.dataset import PatientTrajectory


def build_state_matrix(tables: dict[str, pd.DataFrame]) -> list[PatientTrajectory]:
    """Build a minimal trajectory set from loaded admissions, vitals, and labs."""

    admissions = tables.get("admissions")
    if admissions is None:
        return []

    event_frames = []
    if "vitals_aligned" in tables:
        event_frames.append(_normalize_events(tables["vitals_aligned"], "vital"))
    elif "vitals" in tables:
        event_frames.append(_normalize_events(tables["vitals"], "vital"))
    if "labs" in tables:
        event_frames.append(_normalize_events(tables["labs"], "lab"))

    events = pd.concat(event_frames, ignore_index=True) if event_frames else pd.DataFrame()
    feature_names = sorted(events["feature"].unique()) if not events.empty else []
    trajectories: list[PatientTrajectory] = []

    for admission in admissions.itertuples(index=False):
        subject_id = str(admission.subject_id)
        admission_id = str(admission.hadm_id)
        stay_events = events[
            (events["subject_id"].astype(str) == subject_id)
            & (events["hadm_id"].astype(str) == admission_id)
        ]

        if stay_events.empty:
            timestamps = pd.date_range(admission.admittime, admission.dischtime, periods=2)
            states = np.zeros((len(timestamps), max(1, len(feature_names))), dtype=float)
        else:
            pivot = (
                stay_events.pivot_table(
                    index="charttime",
                    columns="feature",
                    values="valuenum",
                    aggfunc="mean",
                )
                .reindex(columns=feature_names)
                .sort_index()
                .ffill()
                .fillna(0.0)
            )
            timestamps = pivot.index
            states = pivot.to_numpy(dtype=float)

        steps = len(timestamps)
        actions = np.zeros((steps, 1), dtype=int)
        rewards = np.zeros(steps, dtype=float)
        terminals = np.zeros(steps, dtype=bool)
        terminals[-1] = True
        metadata = {
            "died": bool(admission.hospital_expire_flag),
            "feature_names": feature_names,
        }
        trajectories.append(
            PatientTrajectory(
                subject_id=subject_id,
                admission_id=admission_id,
                timestamps=np.array(
                    [pd.Timestamp(ts).timestamp() for ts in timestamps], dtype=float
                ),
                states=states,
                actions=actions,
                rewards=rewards,
                terminals=terminals,
                metadata=metadata,
            )
        )

    return trajectories


def _normalize_events(events: pd.DataFrame, prefix: str) -> pd.DataFrame:
    df = events.copy()
    time_column = "time_bin" if "time_bin" in df.columns else "charttime"
    df = df.rename(columns={time_column: "charttime"})
    df["feature"] = prefix + "_" + df["itemid"].astype(str)
    return df[["subject_id", "hadm_id", "charttime", "feature", "valuenum"]]
