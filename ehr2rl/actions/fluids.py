"""Fluid aggregation helpers for medication actions."""

from __future__ import annotations

import pandas as pd


DEFAULT_FLUID_ITEMIDS = frozenset({225158, 220949})


def fluid_amount(row: pd.Series, fluid_itemids=frozenset(DEFAULT_FLUID_ITEMIDS)) -> float:
    """Return fluid amount in mL for a row, or zero for non-fluid itemids."""

    if int(row.get("itemid", -1)) not in fluid_itemids:
        return 0.0
    amount = pd.to_numeric(row.get("amount", 0.0), errors="coerce")
    if pd.isna(amount):
        return 0.0
    return float(amount)
