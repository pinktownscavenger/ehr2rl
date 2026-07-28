"""Synthetic ehr2rl pipeline example."""

from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset, to_d3rlpy


def main() -> None:
    ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)
    policy = BehaviorPolicy().fit(ds)
    ds = MortalityReward().shape(ds, policy=policy)
    mdp_dataset = to_d3rlpy(ds)
    print(mdp_dataset)


if __name__ == "__main__":
    main()
