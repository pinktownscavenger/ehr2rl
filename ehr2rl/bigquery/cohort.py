"""SQL builders for bounded MIMIC-IV BigQuery cohorts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

HOSP_TABLE = "physionet-data.mimiciv_3_1_hosp"
ICU_TABLE = "physionet-data.mimiciv_3_1_icu"


@dataclass(frozen=True)
class CohortCriteria:
    """Filters that define a bounded ICU cohort.

    Bounds are inclusive. ``None`` or an empty tuple means no filter.

    Parameters
    ----------
    cohort_size
        Maximum number of ICU stays. The first stays by ``subject_id``,
        ``hadm_id``, and ``stay_id`` are taken, not a random sample.
    min_age
        Minimum MIMIC-IV ``anchor_age`` in years.
    max_age
        Maximum MIMIC-IV ``anchor_age`` in years.
    admission_types
        Allowed ``admission_type`` values, such as ``"EW EMER."``.
    min_icu_los_hours
        Minimum ICU length of stay in hours.
    max_icu_los_hours
        Maximum ICU length of stay in hours.

    Raises
    ------
    ValueError
        If ``cohort_size`` is not positive or a bound is negative.
    """

    cohort_size: int = 25
    min_age: int | None = None
    max_age: int | None = None
    admission_types: tuple[str, ...] = ()
    min_icu_los_hours: float | None = None
    max_icu_los_hours: float | None = None

    def __post_init__(self) -> None:
        if self.cohort_size <= 0:
            raise ValueError("cohort_size must be positive.")
        for name in ("min_age", "max_age"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative.")
        for name in ("min_icu_los_hours", "max_icu_los_hours"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative.")


@dataclass(frozen=True)
class BigQueryCohort:
    """Build bounded MIMIC-IV v3.1 SQL queries for a cohort.

    Every query is restricted to the cohort's ICU stays, and event queries keep
    only events during those stays.

    Parameters
    ----------
    criteria
        Cohort filters.
    mimic_version
        Must be ``"3_1"``.

    Raises
    ------
    ValueError
        If ``mimic_version`` is not ``"3_1"``.
    """

    criteria: CohortCriteria
    mimic_version: str = "3_1"

    def __post_init__(self) -> None:
        if self.mimic_version != "3_1":
            raise ValueError("mimic_version must be '3_1' for v0.2 BigQuery cohorts.")

    def admissions_sql(self) -> str:
        """Return SQL for the cohort's admissions rows."""

        return f"""
WITH {self._cohort_cte()}
SELECT
  a.subject_id,
  a.hadm_id,
  a.admittime,
  a.dischtime,
  a.hospital_expire_flag
FROM `{HOSP_TABLE}.admissions` AS a
JOIN (SELECT DISTINCT subject_id, hadm_id FROM cohort) AS c
USING (subject_id, hadm_id)
ORDER BY a.subject_id, a.hadm_id
"""

    def vitals_sql(self, itemids: Iterable[int]) -> str:
        """Return SQL for chartevents rows of the given itemids during cohort stays.

        Parameters
        ----------
        itemids
            Chartevents itemids to select. At least one is required.
        """

        itemid_sql = _itemid_list(itemids)
        return f"""
WITH {self._cohort_cte()}
SELECT
  ce.subject_id,
  ce.hadm_id,
  ce.charttime,
  ce.itemid,
  ce.valuenum
FROM `{ICU_TABLE}.chartevents` AS ce
JOIN cohort AS c
USING (subject_id, hadm_id, stay_id)
WHERE ce.valuenum IS NOT NULL
  AND ce.itemid IN ({itemid_sql})
  AND ce.charttime BETWEEN c.intime AND c.outtime
ORDER BY ce.subject_id, ce.hadm_id, ce.charttime, ce.itemid
"""

    def labs_sql(self, itemids: Iterable[int]) -> str:
        """Return SQL for labevents rows of the given itemids during cohort stays.

        Parameters
        ----------
        itemids
            Labevents itemids to select. At least one is required.
        """

        itemid_sql = _itemid_list(itemids)
        return f"""
WITH {self._cohort_cte()}
SELECT
  le.subject_id,
  le.hadm_id,
  le.charttime,
  le.itemid,
  le.valuenum
FROM `{HOSP_TABLE}.labevents` AS le
JOIN (SELECT DISTINCT subject_id, hadm_id, intime, outtime FROM cohort) AS c
USING (subject_id, hadm_id)
WHERE le.valuenum IS NOT NULL
  AND le.itemid IN ({itemid_sql})
  AND le.charttime BETWEEN c.intime AND c.outtime
ORDER BY le.subject_id, le.hadm_id, le.charttime, le.itemid
"""

    def inputevents_sql(self, itemids: Iterable[int]) -> str:
        """Return SQL for inputevents rows of the given itemids overlapping cohort stays.

        Parameters
        ----------
        itemids
            Inputevents itemids to select. At least one is required.
        """

        itemid_sql = _itemid_list(itemids)
        return f"""
WITH {self._cohort_cte()}
SELECT
  ie.subject_id,
  ie.hadm_id,
  ie.stay_id,
  ie.starttime,
  ie.endtime,
  ie.itemid,
  ie.amount,
  ie.rate,
  ie.rateuom,
  ie.patientweight,
  ie.statusdescription
FROM `{ICU_TABLE}.inputevents` AS ie
JOIN cohort AS c
USING (subject_id, hadm_id, stay_id)
WHERE ie.itemid IN ({itemid_sql})
  AND ie.starttime < c.outtime
  AND ie.endtime > c.intime
ORDER BY ie.subject_id, ie.hadm_id, ie.starttime, ie.itemid
"""

    def _cohort_cte(self) -> str:
        where_clauses = [
            "i.hadm_id IS NOT NULL",
            "i.outtime IS NOT NULL",
        ]
        if self.criteria.admission_types:
            admission_types = ", ".join(
                f"'{value.replace(chr(39), chr(39) + chr(39))}'"
                for value in self.criteria.admission_types
            )
            where_clauses.append(f"a.admission_type IN ({admission_types})")
        if self.criteria.min_icu_los_hours is not None:
            where_clauses.append(
                "TIMESTAMP_DIFF(i.outtime, i.intime, MINUTE) / 60.0 >= "
                f"{float(self.criteria.min_icu_los_hours)}"
            )
        if self.criteria.max_icu_los_hours is not None:
            where_clauses.append(
                "TIMESTAMP_DIFF(i.outtime, i.intime, MINUTE) / 60.0 <= "
                f"{float(self.criteria.max_icu_los_hours)}"
            )
        if self.criteria.min_age is not None or self.criteria.max_age is not None:
            where_clauses.append("p.anchor_age IS NOT NULL")
        if self.criteria.min_age is not None:
            where_clauses.append(f"p.anchor_age >= {int(self.criteria.min_age)}")
        if self.criteria.max_age is not None:
            where_clauses.append(f"p.anchor_age <= {int(self.criteria.max_age)}")

        where_sql = "\n    AND ".join(where_clauses)
        return f"""
cohort AS (
  SELECT i.subject_id, i.hadm_id, i.stay_id, i.intime, i.outtime
  FROM `{ICU_TABLE}.icustays` AS i
  JOIN `{HOSP_TABLE}.admissions` AS a
  USING (subject_id, hadm_id)
  JOIN `{HOSP_TABLE}.patients` AS p
  USING (subject_id)
  WHERE {where_sql}
  ORDER BY i.subject_id, i.hadm_id, i.stay_id
  LIMIT {int(self.criteria.cohort_size)}
)
"""


def _itemid_list(itemids: Iterable[int]) -> str:
    values = tuple(int(itemid) for itemid in itemids)
    if not values:
        raise ValueError("at least one itemid is required.")
    return ", ".join(str(value) for value in values)
