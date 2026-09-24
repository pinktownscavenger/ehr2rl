"""BigQuery-backed smoke loading for credentialed MIMIC-IV validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ehr2rl.data.alignment import align_events
from ehr2rl.data.dataset import EHRDataset


@dataclass(frozen=True)
class BigQuerySmokeResult:
    """Query execution metadata for a bounded smoke-load run."""

    name: str
    bytes_processed: int


def load_mimiciv_smoke_dataset(
    *,
    billing_project: str,
    cohort_size: int = 25,
    maximum_bytes_billed: int = 25_000_000_000,
    location: str | None = None,
) -> EHRDataset:
    """Load a small credentialed MIMIC-IV cohort from BigQuery.

    The loader uses only bounded cohort queries and applies BigQuery's
    ``maximum_bytes_billed`` guard to every query. It is intended for smoke
    validation, not for producing a research cohort.
    """

    if cohort_size <= 0:
        raise ValueError("cohort_size must be positive.")
    if maximum_bytes_billed <= 0:
        raise ValueError("maximum_bytes_billed must be positive.")

    try:
        from google.cloud import bigquery
    except ImportError as exc:  # pragma: no cover - exercised without optional extra
        raise ImportError(
            "Install the BigQuery extra dependencies before using this loader: "
            "google-cloud-bigquery, google-cloud-bigquery-storage, db-dtypes, pyarrow."
        ) from exc

    client = bigquery.Client(project=billing_project, location=location)
    query_stats: list[BigQuerySmokeResult] = []

    admissions = _query_dataframe(
        client,
        _admissions_sql(cohort_size),
        name="admissions",
        maximum_bytes_billed=maximum_bytes_billed,
        query_stats=query_stats,
        bigquery=bigquery,
    )
    vitals = _query_dataframe(
        client,
        _vitals_sql(cohort_size),
        name="vitals",
        maximum_bytes_billed=maximum_bytes_billed,
        query_stats=query_stats,
        bigquery=bigquery,
    )
    labs = _query_dataframe(
        client,
        _labs_sql(cohort_size),
        name="labs",
        maximum_bytes_billed=maximum_bytes_billed,
        query_stats=query_stats,
        bigquery=bigquery,
    )

    admissions = _coerce_admissions(admissions)
    vitals = _coerce_events(vitals)
    labs = _coerce_events(labs)

    ds = EHRDataset()
    ds.tables["admissions"] = admissions
    ds.tables["vitals"] = vitals
    ds.tables["vitals_aligned"] = align_events(vitals, "1h")
    ds.tables["labs"] = labs
    ds.featurize()

    if len(ds) == 0:
        raise RuntimeError("MIMIC-IV BigQuery smoke query returned no trajectories.")

    source_metadata = {
        "billing_project": billing_project,
        "cohort_size": cohort_size,
        "maximum_bytes_billed": maximum_bytes_billed,
        "queries": [result.__dict__ for result in query_stats],
    }
    for trajectory in ds:
        trajectory.metadata["bigquery_source"] = source_metadata

    return ds


def _query_dataframe(
    client: Any,
    sql: str,
    *,
    name: str,
    maximum_bytes_billed: int,
    query_stats: list[BigQuerySmokeResult],
    bigquery: Any,
) -> pd.DataFrame:
    dry_run_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry_run_job = client.query(sql, job_config=dry_run_config)
    if dry_run_job.total_bytes_processed > maximum_bytes_billed:
        raise RuntimeError(
            f"{name} query would process {dry_run_job.total_bytes_processed:,} bytes, "
            f"above the {maximum_bytes_billed:,} byte cap."
        )

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=maximum_bytes_billed,
        use_query_cache=False,
    )
    job = client.query(sql, job_config=job_config)
    df = job.to_dataframe()
    query_stats.append(
        BigQuerySmokeResult(
            name=name,
            bytes_processed=int(job.total_bytes_processed or 0),
        )
    )
    return df


def _cohort_cte(cohort_size: int) -> str:
    return f"""
cohort AS (
  SELECT subject_id, hadm_id, stay_id, intime, outtime
  FROM `physionet-data.mimiciv_3_1_icu.icustays`
  WHERE hadm_id IS NOT NULL
    AND outtime IS NOT NULL
  ORDER BY subject_id, hadm_id, stay_id
  LIMIT {cohort_size}
)
"""


def _admissions_sql(cohort_size: int) -> str:
    return f"""
WITH {_cohort_cte(cohort_size)}
SELECT
  a.subject_id,
  a.hadm_id,
  a.admittime,
  a.dischtime,
  a.hospital_expire_flag
FROM `physionet-data.mimiciv_3_1_hosp.admissions` AS a
JOIN (SELECT DISTINCT subject_id, hadm_id FROM cohort) AS c
USING (subject_id, hadm_id)
ORDER BY a.subject_id, a.hadm_id
"""


def _vitals_sql(cohort_size: int) -> str:
    return f"""
WITH {_cohort_cte(cohort_size)}
SELECT
  ce.subject_id,
  ce.hadm_id,
  ce.charttime,
  ce.itemid,
  ce.valuenum
FROM `physionet-data.mimiciv_3_1_icu.chartevents` AS ce
JOIN cohort AS c
USING (subject_id, hadm_id, stay_id)
WHERE ce.valuenum IS NOT NULL
  AND ce.itemid IN (220045, 220210, 220277, 223761, 223762)
  AND ce.charttime BETWEEN c.intime AND c.outtime
ORDER BY ce.subject_id, ce.hadm_id, ce.charttime, ce.itemid
"""


def _labs_sql(cohort_size: int) -> str:
    return f"""
WITH {_cohort_cte(cohort_size)}
SELECT
  le.subject_id,
  le.hadm_id,
  le.charttime,
  le.itemid,
  le.valuenum
FROM `physionet-data.mimiciv_3_1_hosp.labevents` AS le
JOIN (SELECT DISTINCT subject_id, hadm_id, intime, outtime FROM cohort) AS c
USING (subject_id, hadm_id)
WHERE le.valuenum IS NOT NULL
  AND le.itemid IN (50813, 50912, 51221, 51265, 51301)
  AND le.charttime BETWEEN c.intime AND c.outtime
ORDER BY le.subject_id, le.hadm_id, le.charttime, le.itemid
"""


def _coerce_admissions(admissions: pd.DataFrame) -> pd.DataFrame:
    df = admissions.copy()
    df["admittime"] = pd.to_datetime(df["admittime"], errors="raise")
    df["dischtime"] = pd.to_datetime(df["dischtime"], errors="raise")
    return df


def _coerce_events(events: pd.DataFrame) -> pd.DataFrame:
    df = events.copy()
    df["charttime"] = pd.to_datetime(df["charttime"], errors="raise")
    df["valuenum"] = pd.to_numeric(df["valuenum"], errors="raise")
    return df
