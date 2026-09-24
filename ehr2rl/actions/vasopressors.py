"""Vasopressor dose conversion utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class VasopressorConversion:
    """Conversion factor for norepinephrine-equivalent dose."""

    name: str
    itemids: tuple[int, ...]
    factor: float


DEFAULT_NEE_CONVERSIONS: tuple[VasopressorConversion, ...] = (
    VasopressorConversion("norepinephrine", (221906,), 1.0),
    VasopressorConversion("epinephrine", (221289,), 1.0),
    VasopressorConversion("vasopressin", (222315,), 2.5),
    VasopressorConversion("phenylephrine", (221749,), 0.1),
    VasopressorConversion("dopamine", (221662,), 0.01),
)


def norepinephrine_equivalent(
    row: pd.Series,
    conversions: Iterable[VasopressorConversion] = DEFAULT_NEE_CONVERSIONS,
) -> float:
    """Return norepinephrine-equivalent dose for an inputevents row."""

    itemid = int(row.get("itemid", -1))
    rate = pd.to_numeric(row.get("rate", 0.0), errors="coerce")
    if pd.isna(rate):
        return 0.0
    for conversion in conversions:
        if itemid in conversion.itemids:
            return float(rate) * conversion.factor
    return 0.0
