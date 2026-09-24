import sys
import types

import pandas as pd
import pytest


class FakeQueryJobConfig:
    def __init__(
        self,
        *,
        dry_run=False,
        use_query_cache=True,
        maximum_bytes_billed=None,
    ):
        self.dry_run = dry_run
        self.use_query_cache = use_query_cache
        self.maximum_bytes_billed = maximum_bytes_billed


class FakeJob:
    def __init__(self, *, bytes_processed, dataframe=None, job_id="job_1"):
        self.total_bytes_processed = bytes_processed
        self._dataframe = dataframe
        self.job_id = job_id
        self.to_dataframe_timeout = None

    def to_dataframe(self, timeout=None):
        self.to_dataframe_timeout = timeout
        return self._dataframe.copy()


class FakeBigQueryClient:
    def __init__(self, *, dry_run_bytes, real_dataframe):
        self.dry_run_bytes = dry_run_bytes
        self.real_dataframe = real_dataframe
        self.real_query_count = 0
        self.real_job_config = None
        self.query_timeouts = []
        self.query_retries = []
        self.query_job_retries = []
        self.real_job = None

    def query(self, sql, job_config, timeout=None, retry="default", job_retry="default"):
        _ = sql
        self.query_timeouts.append(timeout)
        self.query_retries.append(retry)
        self.query_job_retries.append(job_retry)
        if job_config.dry_run:
            return FakeJob(bytes_processed=self.dry_run_bytes)
        self.real_query_count += 1
        self.real_job_config = job_config
        self.real_job = FakeJob(
            bytes_processed=self.dry_run_bytes,
            dataframe=self.real_dataframe,
            job_id="real_job",
        )
        return self.real_job


@pytest.fixture(autouse=True)
def fake_bigquery_module(monkeypatch):
    google = types.ModuleType("google")
    cloud = types.ModuleType("google.cloud")
    bigquery = types.ModuleType("google.cloud.bigquery")
    bigquery.QueryJobConfig = FakeQueryJobConfig
    cloud.bigquery = bigquery
    google.cloud = cloud
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.bigquery", bigquery)


def test_guarded_query_blocks_over_budget_before_real_query(tmp_path):
    from ehr2rl.bigquery import BudgetExceededError, GuardedBigQueryClient

    fake = FakeBigQueryClient(dry_run_bytes=101, real_dataframe=pd.DataFrame())
    guarded = GuardedBigQueryClient(fake, maximum_bytes_billed=100, cache_dir=tmp_path)

    with pytest.raises(BudgetExceededError, match="101"):
        guarded.query_dataframe("SELECT 1")

    assert fake.real_query_count == 0


def test_guarded_query_sets_server_side_maximum_bytes(tmp_path):
    from ehr2rl.bigquery import GuardedBigQueryClient

    fake = FakeBigQueryClient(
        dry_run_bytes=50,
        real_dataframe=pd.DataFrame({"x": [1]}),
    )
    guarded = GuardedBigQueryClient(fake, maximum_bytes_billed=100, cache_dir=tmp_path)

    result = guarded.query_dataframe("SELECT 1")

    assert result.bytes_processed == 50
    assert fake.real_job_config.maximum_bytes_billed == 100


def test_guarded_query_cache_hit_avoids_bigquery_call(tmp_path):
    from ehr2rl.bigquery import GuardedBigQueryClient

    fake = FakeBigQueryClient(
        dry_run_bytes=10,
        real_dataframe=pd.DataFrame({"x": [1]}),
    )
    guarded = GuardedBigQueryClient(fake, maximum_bytes_billed=100, cache_dir=tmp_path)

    first = guarded.query_dataframe("SELECT 1", cache_key_parts=("v3_1",))
    second = guarded.query_dataframe("SELECT 1", cache_key_parts=("v3_1",))

    assert first.dataframe.equals(second.dataframe)
    assert fake.real_query_count == 1


def test_guarded_query_cache_hit_does_not_require_bigquery_module(
    tmp_path,
    monkeypatch,
):
    from ehr2rl.bigquery import GuardedBigQueryClient

    fake = FakeBigQueryClient(
        dry_run_bytes=10,
        real_dataframe=pd.DataFrame({"x": [1]}),
    )
    guarded = GuardedBigQueryClient(fake, maximum_bytes_billed=100, cache_dir=tmp_path)
    first = guarded.query_dataframe("SELECT 1", cache_key_parts=("v3_1",))

    monkeypatch.delitem(sys.modules, "google.cloud.bigquery", raising=False)
    monkeypatch.delitem(sys.modules, "google.cloud", raising=False)
    monkeypatch.delitem(sys.modules, "google", raising=False)
    second = guarded.query_dataframe("SELECT 1", cache_key_parts=("v3_1",))

    assert second.dataframe.equals(first.dataframe)
    assert fake.real_query_count == 1


def test_guarded_query_applies_timeout_to_bigquery_calls(tmp_path):
    from ehr2rl.bigquery import GuardedBigQueryClient

    fake = FakeBigQueryClient(
        dry_run_bytes=10,
        real_dataframe=pd.DataFrame({"x": [1]}),
    )
    guarded = GuardedBigQueryClient(
        fake,
        maximum_bytes_billed=100,
        cache_dir=tmp_path,
        query_timeout=3.0,
    )

    guarded.query_dataframe("SELECT 1")

    assert fake.query_timeouts == [3.0, 3.0]
    assert fake.real_job.to_dataframe_timeout == 3.0


def test_guarded_query_can_disable_bigquery_retries(tmp_path):
    from ehr2rl.bigquery import GuardedBigQueryClient

    fake = FakeBigQueryClient(
        dry_run_bytes=10,
        real_dataframe=pd.DataFrame({"x": [1]}),
    )
    guarded = GuardedBigQueryClient(
        fake,
        maximum_bytes_billed=100,
        cache_dir=tmp_path,
        disable_retries=True,
    )

    guarded.query_dataframe("SELECT 1")

    assert fake.query_retries == [None, None]
    assert fake.query_job_retries == [None, None]
