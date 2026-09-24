import pytest


def test_feature_preset_resolves_to_itemids():
    from ehr2rl.data.itemid_maps import load_itemid_map
    from ehr2rl.data.presets import get_feature_preset

    resolved = get_feature_preset("vitals_only").resolve(load_itemid_map("v3_1"))

    assert "heart_rate" in resolved
    assert resolved["heart_rate"][0].itemid == 220045


def test_feature_preset_missing_concept_raises_validation_error():
    from ehr2rl.data.itemid_maps import ItemIdMap
    from ehr2rl.data.loaders import EHRValidationError
    from ehr2rl.data.presets import FeaturePreset

    preset = FeaturePreset(name="bad", concepts=("missing_feature",))

    with pytest.raises(EHRValidationError, match="missing_feature"):
        preset.resolve(ItemIdMap(version="v3_1", concepts={}))


def test_unknown_feature_preset_raises_validation_error():
    from ehr2rl.data.loaders import EHRValidationError
    from ehr2rl.data.presets import get_feature_preset

    with pytest.raises(EHRValidationError, match="unknown"):
        get_feature_preset("unknown")
