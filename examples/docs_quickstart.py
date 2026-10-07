"""Synthetic quickstart shown in the documentation; needs only the base install."""

from __future__ import annotations

import numpy as np

from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset


def main() -> dict[str, int | tuple[int, int]]:
    # 25 deterministic synthetic ICU stays, 24 hourly steps each.
    ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)

    trajectory = ds[0]
    print(trajectory.metadata["feature_names"])  # state columns
    print(trajectory.states.shape)  # (T, D) = (24, 4)
    print(trajectory.actions.shape)  # (T, A) = (24, 1)

    # Estimate how often clinicians took each action in each state.
    policy = BehaviorPolicy().fit(ds)
    all_states = np.vstack([t.states for t in ds])
    probabilities = policy.predict_proba(all_states)
    print(probabilities.shape)  # (25 * 24 timesteps, n_actions) = (600, 2)

    # Terminal reward: +1 for survival, -1 for in-hospital death.
    ds = MortalityReward().shape(ds)
    print(ds[0].rewards[-1])

    summary: dict[str, int | tuple[int, int]] = {
        "n_trajectories": len(ds),
        "state_shape": trajectory.states.shape,
        "probability_rows": probabilities.shape[0],
    }
    print(summary)
    return summary


if __name__ == "__main__":
    main()
