"""Canonical feature presets for MIMIC-IV extraction."""

from __future__ import annotations

from dataclasses import dataclass

from ehr2rl.data.itemid_maps import ItemIdEntry, ItemIdMap
from ehr2rl.data.loaders import EHRValidationError


@dataclass(frozen=True)
class FeaturePreset:
    """Named bundle of canonical feature concepts."""

    name: str
    concepts: tuple[str, ...]
    aggregation: str = "1h"

    def resolve(self, itemid_map: ItemIdMap) -> dict[str, list[ItemIdEntry]]:
        """Resolve canonical concept names to raw itemid entries."""

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
    """Return a built-in feature preset by name."""

    try:
        return _PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(_PRESETS))
        raise EHRValidationError(
            f"unknown feature preset {name!r}; available presets: {available}"
        ) from exc
