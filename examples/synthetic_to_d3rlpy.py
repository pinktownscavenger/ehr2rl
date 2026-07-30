"""Synthetic ehr2rl to d3rlpy IQL smoke example."""

from ehr2rl import BehaviorPolicy, MortalityReward, make_synthetic_dataset, to_d3rlpy


def main() -> None:
    ds = make_synthetic_dataset(n_patients=25, trajectory_length=24, seed=7)

    # IQL in d3rlpy is a continuous-action algorithm. v0.1 uses this
    # deterministic synthetic dose as an example action until real medication
    # action construction lands in v0.2.
    for trajectory in ds:
        mean_bp = trajectory.states[:, 1]
        trajectory.actions = ((140.0 - mean_bp) / 105.0).reshape(-1, 1)

    policy = BehaviorPolicy().fit(ds)
    ds = MortalityReward().shape(ds, policy=policy)
    mdp_dataset = to_d3rlpy(ds)

    import d3rlpy
    from d3rlpy.logging import NoopAdapterFactory

    iql = d3rlpy.algos.IQLConfig(batch_size=16).create(device=False)
    history = iql.fit(
        mdp_dataset,
        n_steps=1,
        n_steps_per_epoch=1,
        logger_adapter=NoopAdapterFactory(),
        save_interval=100,
        show_progress=False,
    )
    print(f"Built {type(mdp_dataset).__name__} and completed {len(history)} IQL step.")


if __name__ == "__main__":
    main()
