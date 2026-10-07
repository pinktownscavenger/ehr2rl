import importlib.util
from pathlib import Path


def test_bigquery_example_imports_without_optional_execution():
    path = Path("examples/bigquery_to_d3rlpy.py")
    spec = importlib.util.spec_from_file_location("bigquery_to_d3rlpy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "main")


def test_documentation_quickstart_runs_without_optional_dependencies():
    path = Path("examples/docs_quickstart.py")
    spec = importlib.util.spec_from_file_location("docs_quickstart", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.main() == {
        "n_trajectories": 25,
        "state_shape": (24, 4),
        "probability_rows": 600,
    }
