"""Synthetic MIMIC-IV-style data for tests and examples."""

from __future__ import annotations

import numpy as np

from ehr2rl.data.dataset import EHRDataset, PatientTrajectory


def make_synthetic_dataset(
    n_patients: int = 100,
    trajectory_length: int = 48,
    seed: int = 42,
) -> EHRDataset:
    """Create a deterministic synthetic dataset with plausible clinical ranges."""

    if n_patients <= 0:
        raise ValueError("n_patients must be positive.")
    if trajectory_length <= 1:
        raise ValueError("trajectory_length must be greater than 1.")

    rng = np.random.default_rng(seed)
    trajectories = []
    base_time = 1_704_067_200.0

    for patient_index in range(n_patients):
        timestamps = base_time + np.arange(trajectory_length) * 3600.0
        heart_rate = rng.normal(85, 15, trajectory_length).clip(35, 180)
        mean_bp = rng.normal(75, 12, trajectory_length).clip(35, 140)
        lactate = rng.lognormal(mean=0.45, sigma=0.35, size=trajectory_length).clip(0.4, 12)
        creatinine = rng.lognormal(mean=0.15, sigma=0.25, size=trajectory_length).clip(0.2, 8)
        states = np.column_stack([heart_rate, mean_bp, lactate, creatinine])

        vasopressor_bin = np.digitize(mean_bp < 65, [0.5]).reshape(-1, 1)
        died = bool(rng.random() < 0.2)
        sofa_scores = _synthetic_sofa(rng, trajectory_length, died)

        rewards = np.zeros(trajectory_length, dtype=float)
        terminals = np.zeros(trajectory_length, dtype=bool)
        terminals[-1] = True
        metadata = {
            "died": died,
            "feature_names": ["heart_rate", "mean_bp", "lactate", "creatinine"],
            "sofa_scores": sofa_scores,
        }

        trajectories.append(
            PatientTrajectory(
                subject_id=f"S{patient_index:05d}",
                admission_id=f"H{patient_index:05d}",
                timestamps=timestamps,
                states=states,
                actions=vasopressor_bin,
                rewards=rewards,
                terminals=terminals,
                metadata=metadata,
            )
        )

    return EHRDataset(trajectories=trajectories)


def _synthetic_sofa(
    rng: np.random.Generator, trajectory_length: int, died: bool
) -> np.ndarray:
    start = rng.integers(2, 9)
    drift = 0.08 if died else -0.04
    noise = rng.normal(drift, 0.5, trajectory_length)
    sofa = np.maximum(0, start + np.cumsum(noise))
    if died:
        sofa[-1] += 3
    return sofa.clip(0, 24)
