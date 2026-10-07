"""Vasopressor dose conversion utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class VasopressorConversion:
    """Conversion factor for norepinephrine-equivalent dose.

    ``factor`` converts a rate expressed in ``rate_unit`` into norepinephrine
    mcg/kg/min.
    """

    name: str
    itemids: tuple[int, ...]
    factor: float
    rate_unit: str = "mcg/kg/min"


DEFAULT_NEE_CONVERSIONS: tuple[VasopressorConversion, ...] = (
    VasopressorConversion("norepinephrine", (221906,), 1.0),
    VasopressorConversion("epinephrine", (221289,), 1.0),
    VasopressorConversion("vasopressin", (222315,), 2.5, rate_unit="units/min"),
    VasopressorConversion("phenylephrine", (221749,), 0.1),
    VasopressorConversion("dopamine", (221662,), 0.01),
)

# Multipliers from a recorded rate unit to each supported target unit. Units
# that are per minute but not per kilogram need the patient's weight.
_UNIT_MULTIPLIERS: dict[str, dict[str, float]] = {
    "mcg/kg/min": {"mcg/kg/min": 1.0, "mg/kg/min": 1000.0},
    "units/min": {"units/min": 1.0, "units/hour": 1.0 / 60.0},
}
_WEIGHT_NORMALIZED_UNITS: dict[str, dict[str, float]] = {
    "mcg/kg/min": {"mcg/min": 1.0, "mg/min": 1000.0},
}


def norepinephrine_equivalent(
    row: pd.Series,
    conversions: Iterable[VasopressorConversion] = DEFAULT_NEE_CONVERSIONS,
) -> float:
    """Return norepinephrine-equivalent dose for an inputevents row.

    The row's ``rateuom`` is converted to the conversion's ``rate_unit`` before
    ``factor`` is applied. Rows without ``rateuom`` are assumed to already be in
    ``rate_unit``. Raises ``ValueError`` for a vasopressor row whose unit cannot
    be converted, rather than returning a dose in the wrong unit.
    """

    itemid = int(row.get("itemid", -1))
    rate = pd.to_numeric(row.get("rate", 0.0), errors="coerce")
    if pd.isna(rate):
        return 0.0
    for conversion in conversions:
        if itemid in conversion.itemids:
            return float(rate) * _unit_multiplier(row, conversion) * conversion.factor
    return 0.0


def _unit_multiplier(row: pd.Series, conversion: VasopressorConversion) -> float:
    recorded = row.get("rateuom")
    if recorded is None or pd.isna(recorded):
        return 1.0
    unit = str(recorded).strip().lower()
    target = conversion.rate_unit.strip().lower()

    multiplier = _UNIT_MULTIPLIERS.get(target, {target: 1.0}).get(unit)
    if multiplier is not None:
        return multiplier

    per_minute = _WEIGHT_NORMALIZED_UNITS.get(target, {}).get(unit)
    if per_minute is not None:
        weight = pd.to_numeric(row.get("patientweight"), errors="coerce")
        if pd.isna(weight) or weight <= 0:
            raise ValueError(
                f"{conversion.name} rate in {recorded} needs a positive "
                "patientweight to convert to mcg/kg/min."
            )
        return per_minute / float(weight)

    raise ValueError(
        f"Cannot convert {conversion.name} (itemid {int(row.get('itemid', -1))}) "
        f"rate unit {recorded!r} to {target}."
    )
