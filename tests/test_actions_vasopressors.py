import numpy as np
import pandas as pd
import pytest


def test_norepinephrine_equivalent_uses_configured_factor():
    from ehr2rl.actions.vasopressors import (
        VasopressorConversion,
        norepinephrine_equivalent,
    )

    row = pd.Series({"itemid": 221289, "rate": 0.1})
    conversions = (VasopressorConversion("epinephrine", (221289,), factor=1.0),)

    assert norepinephrine_equivalent(row, conversions) == pytest.approx(0.1)


def test_norepinephrine_equivalent_unknown_itemid_returns_zero():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    row = pd.Series({"itemid": 999999, "rate": 10.0})

    assert norepinephrine_equivalent(row) == 0.0


def test_norepinephrine_equivalent_missing_rate_returns_zero():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    row = pd.Series({"itemid": 221906})

    assert norepinephrine_equivalent(row) == 0.0


def test_dose_bins_are_right_open_with_zero_bin():
    from ehr2rl.actions.discretize import DoseBins

    bins = DoseBins(edges=(0.0, 0.1, 0.3, 0.6))

    assert bins.assign(np.array([0.0, 0.05, 0.1, 0.6])).tolist() == [0, 1, 2, 4]


def test_vasopressin_units_per_hour_are_converted_to_units_per_minute():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    # 2.4 units/hour = 0.04 units/min, which is 0.1 mcg/kg/min norepinephrine.
    row = pd.Series({"itemid": 222315, "rate": 2.4, "rateuom": "units/hour"})

    assert norepinephrine_equivalent(row) == pytest.approx(0.1)


def test_vasopressin_units_per_minute_use_factor_directly():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    row = pd.Series({"itemid": 222315, "rate": 0.04, "rateuom": "units/min"})

    assert norepinephrine_equivalent(row) == pytest.approx(0.1)


def test_mcg_per_minute_rate_is_normalized_by_patient_weight():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    row = pd.Series(
        {"itemid": 221906, "rate": 8.0, "rateuom": "mcg/min", "patientweight": 80.0}
    )

    assert norepinephrine_equivalent(row) == pytest.approx(0.1)


def test_mcg_per_minute_rate_without_weight_raises():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    row = pd.Series({"itemid": 221906, "rate": 8.0, "rateuom": "mcg/min"})

    with pytest.raises(ValueError, match="patientweight"):
        norepinephrine_equivalent(row)


def test_unknown_rate_unit_for_vasopressor_raises():
    from ehr2rl.actions.vasopressors import norepinephrine_equivalent

    row = pd.Series({"itemid": 221906, "rate": 1.0, "rateuom": "mL/hour"})

    with pytest.raises(ValueError, match="mL/hour"):
        norepinephrine_equivalent(row)


def test_default_vasopressin_factor_applies_per_unit_per_minute():
    from ehr2rl.actions import DEFAULT_NEE_CONVERSIONS

    vasopressin = next(c for c in DEFAULT_NEE_CONVERSIONS if c.name == "vasopressin")

    assert vasopressin.rate_unit == "units/min"
    assert vasopressin.factor == pytest.approx(2.5)


def test_dose_bins_report_number_of_output_values():
    from ehr2rl.actions.discretize import DoseBins

    assert DoseBins(edges=(0.0, 0.1, 0.3, 0.6)).n_bins == 5
    assert DoseBins(edges=(0.0, 0.1), labels=(0, 2, 2)).n_bins == 3
