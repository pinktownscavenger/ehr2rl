import importlib.util
from pathlib import Path


def test_bigquery_example_imports_without_optional_execution():
    path = Path("examples/bigquery_to_d3rlpy.py")
    spec = importlib.util.spec_from_file_location("bigquery_to_d3rlpy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "main")
