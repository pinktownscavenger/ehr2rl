# Features and itemids

MIMIC-IV identifies every charted measurement, lab, and infusion by a numeric
**itemid**. The same clinical idea can have several itemids, and itemids can be
added, retired, or relabelled between releases. `ehr2rl` separates the two
ideas so that code names what it means and the mapping to raw data is explicit
and versioned.

## Concepts, itemid maps, and presets

| Layer | Example | Defined by |
|---|---|---|
| **Concept** | `heart_rate` | A stable canonical name |
| **Itemid map** | `heart_rate` → itemid 220045 in `chartevents`, labelled "Heart Rate" | {py:class}`~ehr2rl.data.itemid_maps.ItemIdMap` |
| **Feature preset** | `vitals_only` = heart rate, respiratory rate, SpO2, temperatures | {py:class}`~ehr2rl.data.FeaturePreset` |

A preset says *which* concepts become state columns. The itemid map says *how*
each concept is found in a specific MIMIC-IV release. Resolving a preset against
a map, with {py:meth}`~ehr2rl.data.FeaturePreset.resolve`, gives the itemids
to query.

Keeping these apart means:

- a preset can be reused against a future MIMIC-IV release by loading a new
  map, without changing analysis code;
- a concept can map to several itemids, which are combined into one feature;
- the map version and preset name are recorded in [provenance](provenance.md),
  so a dataset states exactly which itemids it was built from.

## The built-in map

The `v3_1` itemid map covers MIMIC-IV v3.1 and includes:

- **Vitals** from `chartevents`: heart rate, respiratory rate, SpO2, and
  temperature in °F and °C as separate concepts;
- **Labs** from `labevents`: lactate, creatinine, platelets, WBC, hematocrit;
- **Medications** from `inputevents`: IV fluids and five vasopressors, used to
  build actions rather than states.

Load it with {py:func}`~ehr2rl.data.itemid_maps.load_itemid_map`.

## Validation against live labels

An itemid map records the label each itemid is expected to have. Before every
BigQuery load, {py:func}`~ehr2rl.data.itemid_maps.validate_itemid_map`
compares those labels with MIMIC-IV's `d_items` and `d_labitems` tables,
ignoring case and extra whitespace. A missing itemid or a changed label raises
{py:class}`~ehr2rl.EHRValidationError` before any patient data is queried.

The whole map is validated, including concepts the chosen preset does not use.

## Custom maps

A map file is JSON with a version and a list of entries per concept:

```json
{
  "version": "my_map_v1",
  "concepts": {
    "heart_rate": [
      {"itemid": 220045, "source": "chartevents", "unit": "bpm", "label": "Heart Rate"}
    ]
  }
}
```

Load it with `load_itemid_map(path="my_map.json")` and use a preset whose
concepts all exist in it. Give each map a distinct `version`, because the
version is part of the cache key and the provenance record.

## What is not converted

Entries can carry `unit` and `conversion` fields, but these are descriptive.
States hold values in their recorded units, and no conversion is applied. In
particular, `temperature_f` and `temperature_c` stay separate columns. See
[Limitations](limitations.md).
