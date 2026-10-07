"""Canonical feature presets for MIMIC-IV extraction."""

from __future__ import annotations

from dataclasses import dataclass

from ehr2rl.data.itemid_maps import ItemIdEntry, ItemIdMap
from ehr2rl.data.loaders import EHRValidationError


@dataclass(frozen=True)
class FeaturePreset:
    """A named set of canonical concepts to use as state features.

    Parameters
    ----------
    name
        Preset name, recorded in provenance.
    concepts
        Canonical concept names. Each must exist in the itemid map.
    aggregation
        Intended time resolution. Not currently applied: BigQuery states use
        each distinct chart time.
    """

    name: str
    concepts: tuple[str, ...]
    aggregation: str = "1h"

    def resolve(self, itemid_map: ItemIdMap) -> dict[str, list[ItemIdEntry]]:
        """Map each concept to its itemid entries.

        Parameters
        ----------
        itemid_map
            Map to look the concepts up in.

        Returns
        -------
        dict[str, list[ItemIdEntry]]
            Entries for each concept, in preset order.

        Raises
        ------
        EHRValidationError
            If a concept is missing from the map.
        """

        missing = [
            concept
            for concept in self.concepts
            if concept not in itemid_map.concepts
        ]
        if missing:
            joined = ", ".join(missing)
            raise EHRValidationError(
                f"Feature preset {self.name!r} references missing concepts: {joined}"
            )
        return {
            concept: list(itemid_map.concepts[concept])
            for concept in self.concepts
        }


_PRESETS = {
    "vitals_only": FeaturePreset(
        name="vitals_only",
        concepts=(
            "heart_rate",
            "respiratory_rate",
            "spo2",
            "temperature_f",
            "temperature_c",
        ),
    ),
    "sepsis3_core": FeaturePreset(
        name="sepsis3_core",
        concepts=(
            "heart_rate",
            "respiratory_rate",
            "spo2",
            "temperature_f",
            "temperature_c",
            "lactate",
            "creatinine",
            "platelets",
            "wbc",
        ),
    ),
    "full": FeaturePreset(
        name="full",
        concepts=(
            "heart_rate",
            "respiratory_rate",
            "spo2",
            "temperature_f",
            "temperature_c",
            "lactate",
            "creatinine",
            "platelets",
            "wbc",
            "hematocrit",
        ),
    ),
}


def get_feature_preset(name: str) -> FeaturePreset:
    """Return a built-in feature preset by name.

    Parameters
    ----------
    name
        ``"vitals_only"``, ``"sepsis3_core"``, or ``"full"``.

    Raises
    ------
    EHRValidationError
        If the name is unknown.
    """

    try:
        return _PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(_PRESETS))
        raise EHRValidationError(
            f"unknown feature preset {name!r}; available presets: {available}"
        ) from exc
