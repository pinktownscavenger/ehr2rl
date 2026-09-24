"""Versioned MIMIC-IV itemid maps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

from ehr2rl.data.loaders import EHRValidationError

ItemSource = Literal["chartevents", "labevents", "inputevents"]


@dataclass(frozen=True)
class ItemIdEntry:
    """One raw MIMIC itemid mapped to a canonical concept."""

    itemid: int
    source: ItemSource
    unit: str | None = None
    label: str | None = None
    conversion: str | None = None


@dataclass(frozen=True)
class ItemIdMap:
    """A versioned mapping from canonical concepts to raw itemids."""

    version: str
    concepts: dict[str, list[ItemIdEntry]]


def load_itemid_map(
    version: str = "v3_1",
    path: str | Path | None = None,
) -> ItemIdMap:
    """Load a built-in or user-supplied itemid map."""

    map_path = Path(path) if path is not None else _builtin_map_path(version)
    with map_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    concepts = {
        concept: [ItemIdEntry(**entry) for entry in entries]
        for concept, entries in raw["concepts"].items()
    }
    return ItemIdMap(version=str(raw["version"]), concepts=concepts)


def validate_itemid_map(itemid_map: ItemIdMap, labels: pd.DataFrame) -> None:
    """Validate mapped itemids against live MIMIC label tables."""

    required = {"itemid", "label"}
    missing_columns = required - set(labels.columns)
    if missing_columns:
        joined = ", ".join(sorted(missing_columns))
        raise EHRValidationError(f"label table is missing columns: {joined}")

    label_lookup = {
        int(row.itemid): str(row.label)
        for row in labels[["itemid", "label"]].itertuples(index=False)
    }
    for concept, entries in itemid_map.concepts.items():
        for entry in entries:
            actual_label = label_lookup.get(entry.itemid)
            if actual_label is None:
                raise EHRValidationError(
                    f"{concept} itemid {entry.itemid} is missing from label table."
                )
            if entry.label is not None and _normalize_label(actual_label) != _normalize_label(
                entry.label
            ):
                raise EHRValidationError(
                    f"{concept} itemid {entry.itemid} label changed: "
                    f"expected {entry.label!r}, found {actual_label!r}."
                )


def _builtin_map_path(version: str) -> Path:
    path = Path(__file__).with_suffix("") / f"{version}.yaml"
    if not path.exists():
        raise EHRValidationError(f"Unknown itemid map version: {version}")
    return path


def _normalize_label(label: str) -> str:
    return " ".join(label.casefold().split())
