import pytest


def test_vitals_sql_filters_chartevents_by_cohort_and_time_range():
    from ehr2rl.bigquery import BigQueryCohort, CohortCriteria

    cohort = BigQueryCohort(CohortCriteria(cohort_size=10))
    sql = cohort.vitals_sql([220045, 220210])

    assert "`physionet-data.mimiciv_3_1_icu.chartevents`" in sql
    assert "JOIN cohort" in sql
    assert "ce.charttime BETWEEN c.intime AND c.outtime" in sql
    assert "ce.itemid IN (220045, 220210)" in sql


def test_event_sql_has_deterministic_ordering():
    from ehr2rl.bigquery import BigQueryCohort, CohortCriteria

    cohort = BigQueryCohort(CohortCriteria(cohort_size=10))

    assert "ORDER BY ce.subject_id, ce.hadm_id, ce.charttime" in cohort.vitals_sql([1])
    assert "ORDER BY le.subject_id, le.hadm_id, le.charttime" in cohort.labs_sql([1])
    assert (
        "ORDER BY ie.subject_id, ie.hadm_id, ie.starttime"
        in cohort.inputevents_sql([1])
    )


def test_cohort_criteria_requires_positive_size():
    from ehr2rl.bigquery import CohortCriteria

    with pytest.raises(ValueError, match="cohort_size"):
        CohortCriteria(cohort_size=0)


def test_bigquery_cohort_rejects_unsupported_mimic_version():
    from ehr2rl.bigquery import BigQueryCohort, CohortCriteria

    with pytest.raises(ValueError, match="mimic_version"):
        BigQueryCohort(CohortCriteria(cohort_size=10), mimic_version="2_2")
