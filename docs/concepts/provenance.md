# Provenance

An offline RL dataset built from health records is only as trustworthy as the
record of how it was built. Every BigQuery-backed trajectory carries
`metadata["provenance"]`, and {py:func}`~ehr2rl.to_d3rlpy` can write it beside
the exported dataset as a JSON sidecar.

## What is recorded

{py:class}`~ehr2rl.provenance.DatasetProvenance` holds:

| Field | What it identifies |
|---|---|
| `bigquery_job_ids` | The BigQuery jobs that ran, for lookup in the Cloud console |
| `query_hash` | The exact SQL and cache keys of each query, joined with `:` |
| `itemid_map_version` | Which itemid map translated concepts to itemids |
| `feature_preset` | Which concepts became state columns |
| `extraction_timestamp` | When the load ran, in UTC |
| `mimic_version` | The MIMIC-IV release queried |

Together these identify the cohort SQL, the features, and the data release.
The cohort definition itself is part of the SQL, so it is covered by
`query_hash`.

## How it is computed

Each query returns a SHA-256 hash of its SQL text and cache key parts. The
pipeline joins the hashes of the admissions, feature, and inputevents queries
in order. Two loads with the same `query_hash` ran the same queries.

Job IDs are recorded only for queries that actually ran. Results served from
the local cache have no job, so a fully cached load has an empty
`bigquery_job_ids` list. The query hash is the reliable identifier; job IDs
are for audit.

## Writing and reading sidecars

```python
from ehr2rl import to_d3rlpy
from ehr2rl.provenance import read_provenance

mdp_dataset = to_d3rlpy(ds, provenance_path="dataset.provenance.json")
provenance = read_provenance("dataset.provenance.json")
```

Every trajectory in the dataset must carry identical provenance. Mixing
trajectories from different loads raises `ValueError`, because one sidecar
could not describe them truthfully. Synthetic datasets carry no provenance.

## What provenance does not cover

- **Reward and policy choices.** These are applied after loading. Record them
  separately.
- **Changes you make to trajectories** after loading, such as edited metadata
  or filtered trajectories.
- **Upstream data changes within a release.** `mimic_version` names the
  release, and label validation catches relabelled itemids, but provenance
  does not checksum the data returned.
