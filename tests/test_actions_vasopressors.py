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
