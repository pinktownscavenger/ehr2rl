"""Guarded BigQuery query execution."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import pandas as pd

from ehr2rl.bigquery.errors import BigQueryAuthError, BudgetExceededError


@dataclass(frozen=True)
class QueryResult:
    """Dataframe plus BigQuery execution metadata."""

    dataframe: pd.DataFrame
    job_id: str | None
    bytes_processed: int
    query_hash: str


class GuardedBigQueryClient:
    """Run BigQuery queries only after an explicit dry-run budget check."""

    def __init__(
        self,
        client: Any,
        maximum_bytes_billed: int,
        cache_dir: str | Path | None = None,
    ) -> None:
        if maximum_bytes_billed <= 0:
            raise ValueError("maximum_bytes_billed must be positive.")
        self.client = client
        self.maximum_bytes_billed = maximum_bytes_billed
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def query_dataframe(
        self,
        sql: str,
        *,
        cache_key_parts: tuple[str, ...] = (),
    ) -> QueryResult:
        """Return a dataframe for ``sql`` after dry-run and cache checks."""

        query_hash = _query_hash(sql, cache_key_parts)
        cached = self._read_cache(query_hash)
        if cached is not None:
            return QueryResult(
                dataframe=cached,
                job_id=None,
                bytes_processed=0,
                query_hash=query_hash,
            )

        from google.cloud import bigquery

        try:
            dry_run_config = bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False,
            )
            dry_run_job = self.client.query(sql, job_config=dry_run_config)
        except Exception as exc:  # pragma: no cover - depends on google exceptions
            raise BigQueryAuthError(f"BigQuery dry run failed: {exc}") from exc

        bytes_processed = int(dry_run_job.total_bytes_processed or 0)
        if bytes_processed > self.maximum_bytes_billed:
            raise BudgetExceededError(
                f"Query would process {bytes_processed:,} bytes, above the "
                f"{self.maximum_bytes_billed:,} byte cap."
            )

        try:
            job_config = bigquery.QueryJobConfig(
                maximum_bytes_billed=self.maximum_bytes_billed,
                use_query_cache=False,
            )
            job = self.client.query(sql, job_config=job_config)
            dataframe = job.to_dataframe()
        except Exception as exc:  # pragma: no cover - depends on google exceptions
            raise BigQueryAuthError(f"BigQuery query failed: {exc}") from exc

        self._write_cache(query_hash, dataframe)
        return QueryResult(
            dataframe=dataframe,
            job_id=getattr(job, "job_id", None),
            bytes_processed=bytes_processed,
            query_hash=query_hash,
        )

    def _read_cache(self, query_hash: str) -> pd.DataFrame | None:
        if self.cache_dir is None:
            return None
        parquet_path = self.cache_dir / f"{query_hash}.parquet"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        pickle_path = self.cache_dir / f"{query_hash}.pkl"
        if pickle_path.exists():
            return pd.read_pickle(pickle_path)
        return None

    def _write_cache(self, query_hash: str, dataframe: pd.DataFrame) -> None:
        if self.cache_dir is None:
            return
        parquet_path = self.cache_dir / f"{query_hash}.parquet"
        try:
            dataframe.to_parquet(parquet_path, index=False)
        except ImportError:
            dataframe.to_pickle(self.cache_dir / f"{query_hash}.pkl")


def _query_hash(sql: str, cache_key_parts: tuple[str, ...]) -> str:
    digest = sha256()
    digest.update(sql.encode("utf-8"))
    for part in cache_key_parts:
        digest.update(b"\0")
        digest.update(part.encode("utf-8"))
    return digest.hexdigest()
