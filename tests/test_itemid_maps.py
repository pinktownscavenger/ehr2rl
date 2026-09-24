import pandas as pd
import pytest


def test_load_builtin_v31_itemid_map_has_core_concepts():
    from ehr2rl.data.itemid_maps import load_itemid_map

    item_map = load_itemid_map("v3_1")

    assert item_map.version == "v3_1"
    assert "heart_rate" in item_map.concepts
    assert any(
        entry.source == "chartevents"
        for entry in item_map.concepts["heart_rate"]
    )


def test_validate_itemid_map_rejects_missing_label():
    from ehr2rl.data.itemid_maps import ItemIdEntry, ItemIdMap, validate_itemid_map
    from ehr2rl.data.loaders import EHRValidationError

    item_map = ItemIdMap(
        version="v3_1",
        concepts={
            "heart_rate": [
                ItemIdEntry(
                    itemid=220045,
                    source="chartevents",
                    label="Heart Rate",
                )
            ]
        },
    )
    labels = pd.DataFrame({"itemid": [999999], "label": ["Other"]})

    with pytest.raises(EHRValidationError, match="220045"):
        validate_itemid_map(item_map, labels)


def test_validate_itemid_map_rejects_label_drift():
    from ehr2rl.data.itemid_maps import ItemIdEntry, ItemIdMap, validate_itemid_map
    from ehr2rl.data.loaders import EHRValidationError

    item_map = ItemIdMap(
        version="v3_1",
        concepts={
            "heart_rate": [
                ItemIdEntry(
                    itemid=220045,
                    source="chartevents",
                    label="Heart Rate",
                )
            ]
        },
    )
    labels = pd.DataFrame({"itemid": [220045], "label": ["Heart Rhythm"]})

    with pytest.raises(EHRValidationError, match="label changed"):
        validate_itemid_map(item_map, labels)
