"""Errors raised by BigQuery-backed ehr2rl components."""


class BigQueryError(RuntimeError):
    """Base error for ehr2rl BigQuery operations."""


class BudgetExceededError(BigQueryError):
    """Raised before execution when a dry run exceeds the configured budget."""


class BigQueryAuthError(BigQueryError):
    """Raised when a BigQuery dry run or query fails.

    Despite the name, this covers every failure from the BigQuery client,
    including invalid SQL, timeouts, and network errors, not only
    authentication and permissions.
    """
