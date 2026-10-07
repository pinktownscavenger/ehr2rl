# Extending ehr2rl

Each extension below lists the files that usually change. Every change follows
the same order:

1. Write a failing test in the matching test file.
2. Implement until it passes.
3. Export the object, if it is public, by adding it to `__all__` and to the
   `PUBLIC_API` list in `tests/test_public_docs.py`.
4. Document it on its API page and, if users need to know, in a guide.

Do not add an object to `__all__` before it has tests. Once exported, it is
part of the supported API.

## Adding features and itemids

New state features are new **concepts** in an itemid map. See
[Features and itemids](../concepts/features-and-itemids.md).

| Change | Where |
|---|---|
| Add the concept and its itemids, with expected labels | `ehr2rl/data/itemid_maps/v3_1.yaml` |
| Add it to a preset, or add a preset | `_PRESETS` in `ehr2rl/data/presets.py` |
| Test resolution and validation | `tests/test_feature_presets.py`, `tests/test_itemid_maps.py` |
| Document the preset | `docs/use/bigquery.md` preset table |

Always fill in `label` so live validation can catch relabelled itemids. Check
labels against `d_items` or `d_labitems` before committing. The label check
runs against the whole map on every load, so a wrong label breaks every user.

Only `chartevents` and `labevents` concepts become states. `inputevents`
concepts feed actions.

## Adding an action representation

| Change | Where |
|---|---|
| Dose conversion or aggregation | `ehr2rl/actions/vasopressors.py`, `fluids.py`, `medications.py` |
| Configuration | `ActionConfig` in `ehr2rl/actions/medications.py` |
| Wiring into loading | `load_mimiciv_bigquery_dataset` in `ehr2rl/bigquery/pipeline.py` |
| Tests | `tests/test_medication_actions.py`, `tests/test_actions_vasopressors.py` |
| Docs | `docs/use/actions.md`, `docs/api/actions.md` |

Discrete actions must record `metadata["action_sizes"]` on every trajectory so
the exporter can declare the full action space. New vasopressor units need an
entry in the unit tables in `vasopressors.py` and a test. Never return a dose
in an unconverted unit.

## Adding a reward

| Change | Where |
|---|---|
| A `BaseReward` subclass implementing `compute` | New module in `ehr2rl/reward/` |
| Export | `ehr2rl/reward/__init__.py`, and `ehr2rl/__init__.py` if commonly used |
| Tests | `tests/test_reward.py` or a new `tests/test_<name>_reward.py` |
| Docs | `docs/use/rewards.md`, `docs/api/rewards.md`, and the metadata table in `docs/concepts/reward-semantics.md` |

`compute` must return shape `(T,)` and must not modify the trajectory. Raise
`ValueError` with the missing key's name when required metadata is absent, and
document which loaders provide it.

## Adding an exporter

| Change | Where |
|---|---|
| A `to_<library>` function | New module in `ehr2rl/export/` |
| Optional dependency | A new extra in `pyproject.toml`, also added to `all` |
| Export | `ehr2rl/export/__init__.py` |
| Tests | `tests/test_export.py` or a new test file, skipping when the extra is missing |
| Docs | A guide in `docs/use/`, a page in `docs/api/`, and the installation table |

Import the library inside the function and raise an `ImportError` naming the
extra, so the base install and the docs build keep working. Reuse the
`to_d3rlpy` action handling: integer actions with `action_sizes` are discrete,
floats are continuous.
