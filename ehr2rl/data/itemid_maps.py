"""Versioned MIMIC-IV itemid maps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

from ehr2rl.data.loaders import EHRValidationError

__all__ = ["ItemIdEntry", "ItemIdMap", "load_itemid_map", "validate_itemid_map"]

ItemSource = Literal["chartevents", "labevents", "inputevents"]


@dataclass(frozen=True)
class ItemIdEntry:
    """One raw MIMIC-IV itemid mapped to a canonical concept.

    Parameters
    ----------
    itemid
        MIMIC-IV itemid.
    source
        Table the itemid comes from: ``"chartevents"``, ``"labevents"``, or
        ``"inputevents"``.
    unit
        Recorded unit, for reference.
    label
        Expected label in ``d_items`` or ``d_labitems``, checked by
        `validate_itemid_map` when set.
    conversion
        Name of an intended unit conversion. Informational only; not applied.
    """

    itemid: int
    source: ItemSource
    unit: str | None = None
    label: str | None = None
    conversion: str | None = None


@dataclass(frozen=True)
class ItemIdMap:
    """A versioned mapping from canonical concepts to raw itemids.

    Parameters
    ----------
    version
        Map version, such as ``"v3_1"``, recorded in provenance.
    concepts
        Itemid entries for each concept name.
    """

    version: str
    concepts: dict[str, list[ItemIdEntry]]


def load_itemid_map(
    version: str = "v3_1",
    path: str | Path | None = None,
) -> ItemIdMap:
    """Load a built-in or user-supplied itemid map.

    Map files are JSON with a ``version`` string and a ``concepts`` object that
    maps each concept name to a list of entries with `ItemIdEntry` fields.

    Parameters
    ----------
    version
        Built-in map to load. Only ``"v3_1"`` ships with the package.
    path
        A map file to load instead. ``version`` is ignored when it is given.

    Raises
    ------
    EHRValidationError
        If ``version`` names no built-in map.
    """

    map_path = Path(path) if path is not None else _builtin_map_path(version)
    with map_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    concepts = {
        concept: [ItemIdEntry(**entry) for entry in entries]
        for concept, entries in raw["concepts"].items()
    }
    return ItemIdMap(version=str(raw["version"]), concepts=concepts)


def validate_itemid_map(itemid_map: ItemIdMap, labels: pd.DataFrame) -> None:
    """Check every itemid in a map against live MIMIC-IV labels.

    Labels are compared case-insensitively with whitespace collapsed. Entries
    without an expected ``label`` only need to exist.

    Parameters
    ----------
    itemid_map
        Map to check. Every concept is checked, not only those in a preset.
    labels
        Rows from ``d_items`` and ``d_labitems`` with ``itemid`` and
        ``label`` columns.

    Raises
    ------
    EHRValidationError
        If ``labels`` lacks a required column, an itemid is missing, or a label
        differs.
    """

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
