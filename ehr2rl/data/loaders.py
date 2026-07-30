"""CSV loading and schema validation."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd


class EHRValidationError(ValueError):
    """Raised when an input EHR table does not match the expected schema."""


ADMISSIONS_COLUMNS = {
    "subject_id",
    "hadm_id",
    "admittime",
    "dischtime",
    "hospital_expire_flag",
}
VITALS_COLUMNS = {"subject_id", "hadm_id", "charttime", "itemid", "valuenum"}
LABS_COLUMNS = {"subject_id", "hadm_id", "charttime", "itemid", "valuenum"}


def load_admissions(path: str | Path) -> pd.DataFrame:
    df = _read_csv(path)
    _require_columns(df, ADMISSIONS_COLUMNS, "admissions")
    for column in ("admittime", "dischtime"):
        df[column] = pd.to_datetime(df[column], errors="raise")
    return df


def load_vitals(path: str | Path) -> pd.DataFrame:
    df = _read_csv(path)
    _require_columns(df, VITALS_COLUMNS, "vitals")
    df["charttime"] = pd.to_datetime(df["charttime"], errors="raise")
    df["valuenum"] = pd.to_numeric(df["valuenum"], errors="raise")
    return df


def load_labs(path: str | Path) -> pd.DataFrame:
    df = _read_csv(path)
    _require_columns(df, LABS_COLUMNS, "labs")
    df["charttime"] = pd.to_datetime(df["charttime"], errors="raise")
    df["valuenum"] = pd.to_numeric(df["valuenum"], errors="raise")
    return df


def _read_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise EHRValidationError(f"Input table does not exist: {path}")
    return pd.read_csv(path)


def _require_columns(
    df: pd.DataFrame, required: Iterable[str], table_name: str
) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        joined = ", ".join(missing)
        raise EHRValidationError(f"{table_name} table is missing columns: {joined}")
