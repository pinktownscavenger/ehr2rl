# BigQuery

Requires `pip install "ehr2rl[bigquery]"`. See the
[BigQuery guide](../use/bigquery.md) for prerequisites, costs, and limits.

## Loading a dataset

```{eval-rst}
.. autofunction:: ehr2rl.bigquery.load_mimiciv_bigquery_dataset
```

## Cohorts

```{eval-rst}
.. autoclass:: ehr2rl.bigquery.CohortCriteria
```

```{eval-rst}
.. autoclass:: ehr2rl.bigquery.BigQueryCohort
   :members: admissions_sql, vitals_sql, labs_sql, inputevents_sql
```

## Guarded execution

```{eval-rst}
.. autoclass:: ehr2rl.bigquery.GuardedBigQueryClient
   :members: query_dataframe
```

```{eval-rst}
.. autoclass:: ehr2rl.bigquery.QueryResult
```

## Errors

```{eval-rst}
.. autoexception:: ehr2rl.bigquery.BigQueryError
```

```{eval-rst}
.. autoexception:: ehr2rl.bigquery.BudgetExceededError
```

```{eval-rst}
.. autoexception:: ehr2rl.bigquery.BigQueryAuthError
```
