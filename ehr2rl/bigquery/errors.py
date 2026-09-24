"""Errors raised by BigQuery-backed ehr2rl components."""


class BigQueryError(RuntimeError):
    """Base error for ehr2rl BigQuery operations."""


class BudgetExceededError(BigQueryError):
    """Raised before execution when a dry run exceeds the configured budget."""


class BigQueryAuthError(BigQueryError):
    """Raised when BigQuery authentication or permission checks fail."""
