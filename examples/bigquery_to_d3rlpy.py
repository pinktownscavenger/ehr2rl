"""Bounded MIMIC-IV BigQuery to d3rlpy example."""

from __future__ import annotations

import os
from pathlib import Path

COHORT_SIZE = 25
MAXIMUM_BYTES_BILLED = 25_000_000_000


def main() -> None:
    """Run a bounded BigQuery extraction and one d3rlpy training step."""

    billing_project = os.getenv("EHR2RL_BIGQUERY_BILLING_PROJECT")
    if not billing_project:
        raise SystemExit("Set EHR2RL_BIGQUERY_BILLING_PROJECT before running this example.")

    try:
        from d3rlpy.algos import IQLConfig
        from google.cloud import bigquery
    except ImportError as exc:
        raise SystemExit(
            "Install optional dependencies first: pip install 'ehr2rl[all]'."
        ) from exc

    from ehr2rl import CompositeReward, MortalityReward, SofaReward, to_d3rlpy
    from ehr2rl.actions import ActionConfig, DoseBins
    from ehr2rl.bigquery import (
        BigQueryCohort,
        CohortCriteria,
        GuardedBigQueryClient,
        load_mimiciv_bigquery_dataset,
    )
    from ehr2rl.data.itemid_maps import load_itemid_map
    from ehr2rl.data.presets import get_feature_preset

    client = GuardedBigQueryClient(
        bigquery.Client(project=billing_project),
        maximum_bytes_billed=MAXIMUM_BYTES_BILLED,
        cache_dir=Path(".ehr2rl_cache"),
    )
    dataset = load_mimiciv_bigquery_dataset(
        client=client,
        cohort=BigQueryCohort(CohortCriteria(cohort_size=COHORT_SIZE)),
        preset=get_feature_preset("vitals_only"),
        itemid_map=load_itemid_map("v3_1"),
        action_config=ActionConfig(
            vasopressor_bins=DoseBins(edges=(0.0, 0.1, 0.3, 0.6)),
            fluid_bins=DoseBins(edges=(0.0, 250.0, 500.0, 1000.0)),
        ),
    )
    reward = CompositeReward([(MortalityReward(), 1.0), (SofaReward(), 0.0)])
    for trajectory in dataset:
        trajectory.metadata.setdefault("sofa_scores", [0.0] * trajectory.n_steps)
    dataset = reward.shape(dataset)
    mdp_dataset = to_d3rlpy(dataset, provenance_path="bigquery_to_d3rlpy.provenance.json")

    algorithm = IQLConfig().create(device=False)
    algorithm.fit(mdp_dataset, n_steps=1)


if __name__ == "__main__":
    main()
