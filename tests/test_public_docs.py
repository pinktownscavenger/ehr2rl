"""Public API objects must be exported and carry descriptive docstrings."""

from __future__ import annotations

import importlib
import inspect

import pytest

# (module path the docs present the object under, object name)
PUBLIC_API = [
    ("ehr2rl", "PatientTrajectory"),
    ("ehr2rl", "EHRDataset"),
    ("ehr2rl", "EHRValidationError"),
    ("ehr2rl", "make_synthetic_dataset"),
    ("ehr2rl", "MortalityReward"),
    ("ehr2rl", "SofaReward"),
    ("ehr2rl", "ReadmissionReward"),
    ("ehr2rl", "CompositeReward"),
    ("ehr2rl", "BehaviorPolicy"),
    ("ehr2rl", "to_d3rlpy"),
    ("ehr2rl.data", "FeaturePreset"),
    ("ehr2rl.data", "get_feature_preset"),
    ("ehr2rl.data", "load_mimiciv_smoke_dataset"),
    ("ehr2rl.data.itemid_maps", "ItemIdEntry"),
    ("ehr2rl.data.itemid_maps", "ItemIdMap"),
    ("ehr2rl.data.itemid_maps", "load_itemid_map"),
    ("ehr2rl.data.itemid_maps", "validate_itemid_map"),
    ("ehr2rl.bigquery", "CohortCriteria"),
    ("ehr2rl.bigquery", "BigQueryCohort"),
    ("ehr2rl.bigquery", "GuardedBigQueryClient"),
    ("ehr2rl.bigquery", "QueryResult"),
    ("ehr2rl.bigquery", "load_mimiciv_bigquery_dataset"),
    ("ehr2rl.bigquery", "BigQueryError"),
    ("ehr2rl.bigquery", "BigQueryAuthError"),
    ("ehr2rl.bigquery", "BudgetExceededError"),
    ("ehr2rl.actions", "DoseBins"),
    ("ehr2rl.actions", "ActionConfig"),
    ("ehr2rl.actions", "build_medication_actions"),
    ("ehr2rl.actions", "VasopressorConversion"),
    ("ehr2rl.actions", "DEFAULT_NEE_CONVERSIONS"),
    ("ehr2rl.actions", "norepinephrine_equivalent"),
    ("ehr2rl.reward", "BaseReward"),
    ("ehr2rl.provenance", "DatasetProvenance"),
    ("ehr2rl.provenance", "read_provenance"),
    ("ehr2rl.provenance", "write_provenance"),
]

# Public methods and properties documented on the API pages.
PUBLIC_MEMBERS = {
    "PatientTrajectory": ["n_steps", "with_rewards"],
    "EHRDataset": ["copy_with", "load_admissions", "load_vitals", "load_labs", "featurize"],
    "FeaturePreset": ["resolve"],
    "BigQueryCohort": ["admissions_sql", "vitals_sql", "labs_sql", "inputevents_sql"],
    "GuardedBigQueryClient": ["query_dataframe"],
    "DoseBins": ["n_bins", "assign"],
    "BaseReward": ["compute", "shape"],
    "MortalityReward": ["compute"],
    "SofaReward": ["compute"],
    "ReadmissionReward": ["compute"],
    "CompositeReward": ["compute"],
    "BehaviorPolicy": ["fit", "predict_proba", "propensity_scores"],
}

# Data constants have no docstring of their own; autodoc reads a #: comment.
CONSTANTS = {"DEFAULT_NEE_CONVERSIONS"}


def _resolve(module_path: str, name: str) -> object:
    return getattr(importlib.import_module(module_path), name)


def _has_parameters(obj: object) -> bool:
    target = obj.__init__ if inspect.isclass(obj) else obj
    try:
        parameters = inspect.signature(target).parameters
    except (TypeError, ValueError):
        return False
    return any(name not in {"self", "args", "kwargs"} for name in parameters)


def _assert_descriptive(label: str, obj: object, *, is_class: bool) -> None:
    doc = inspect.getdoc(obj)
    assert doc, f"{label} has no docstring"
    summary = doc.splitlines()[0].strip()
    assert summary.endswith("."), f"{label} summary should be one full sentence"
    # Dataclasses without a docstring get an auto-generated signature instead.
    assert not summary.startswith(f"{getattr(obj, '__name__', '')}("), (
        f"{label} only has an auto-generated dataclass docstring"
    )
    if _has_parameters(obj):
        sections = ("Parameters", "Attributes") if is_class else ("Parameters",)
        assert any(section in doc for section in sections), (
            f"{label} takes arguments but documents none of {sections}"
        )


@pytest.mark.parametrize(("module_path", "name"), PUBLIC_API)
def test_documented_objects_are_exported(module_path: str, name: str) -> None:
    assert name in importlib.import_module(module_path).__all__


def test_internal_helpers_are_not_exported() -> None:
    assert "provenance_from_mapping" not in importlib.import_module("ehr2rl.provenance").__all__
    assert "arrays_for_d3rlpy" not in importlib.import_module("ehr2rl.export").__all__


@pytest.mark.parametrize(
    ("module_path", "name"),
    [entry for entry in PUBLIC_API if entry[1] not in CONSTANTS],
)
def test_public_objects_have_descriptive_docstrings(module_path: str, name: str) -> None:
    obj = _resolve(module_path, name)
    _assert_descriptive(f"{module_path}.{name}", obj, is_class=inspect.isclass(obj))


@pytest.mark.parametrize(
    ("class_name", "member"),
    [(cls, member) for cls, members in PUBLIC_MEMBERS.items() for member in members],
)
def test_public_members_have_descriptive_docstrings(class_name: str, member: str) -> None:
    module_path = next(path for path, name in PUBLIC_API if name == class_name)
    attribute = inspect.getattr_static(_resolve(module_path, class_name), member)
    if isinstance(attribute, property):
        target: object = attribute.fget
    else:
        target = getattr(_resolve(module_path, class_name), member)
    _assert_descriptive(f"{class_name}.{member}", target, is_class=False)
