"""Dataset provenance sidecar helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetProvenance:
    """Metadata needed to reproduce a BigQuery-backed dataset extraction."""

    bigquery_job_ids: tuple[str, ...]
    query_hash: str
    itemid_map_version: str
    feature_preset: str
    extraction_timestamp: str
    mimic_version: str


def write_provenance(path: str | Path, provenance: DatasetProvenance) -> None:
    """Write provenance metadata as JSON."""

    data = asdict(provenance)
    data["bigquery_job_ids"] = list(provenance.bigquery_job_ids)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_provenance(path: str | Path) -> DatasetProvenance:
    """Read and validate provenance metadata from JSON."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return provenance_from_mapping(data)


def provenance_from_mapping(data: dict[str, Any]) -> DatasetProvenance:
    """Build provenance from a metadata dictionary."""

    required = {
        "bigquery_job_ids",
        "query_hash",
        "itemid_map_version",
        "feature_preset",
        "extraction_timestamp",
        "mimic_version",
    }
    missing = sorted(required - set(data))
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"provenance metadata is missing fields: {joined}")
    return DatasetProvenance(
        bigquery_job_ids=tuple(str(job_id) for job_id in data["bigquery_job_ids"]),
        query_hash=str(data["query_hash"]),
        itemid_map_version=str(data["itemid_map_version"]),
        feature_preset=str(data["feature_preset"]),
        extraction_timestamp=str(data["extraction_timestamp"]),
        mimic_version=str(data["mimic_version"]),
    )
