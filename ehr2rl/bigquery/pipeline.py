"""BigQuery-to-EHRDataset assembly."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ehr2rl.actions import ActionConfig, build_medication_actions
from ehr2rl.bigquery.client import GuardedBigQueryClient, QueryResult
from ehr2rl.bigquery.cohort import BigQueryCohort
from ehr2rl.data.dataset import EHRDataset
from ehr2rl.data.featurize import build_state_matrix
from ehr2rl.data.itemid_maps import ItemIdEntry, ItemIdMap, validate_itemid_map
from ehr2rl.data.presets import FeaturePreset


def load_mimiciv_bigquery_dataset(
    client: GuardedBigQueryClient,
    cohort: BigQueryCohort,
    preset: FeaturePreset,
    itemid_map: ItemIdMap,
    action_config: ActionConfig,
) -> EHRDataset:
    """Load a bounded MIMIC-IV cohort from BigQuery into an ``EHRDataset``.

    Validates the itemid map against live labels, then queries admissions, the
    preset's chartevents and labevents, and inputevents for medication actions.
    Every query goes through ``client``'s budget guard.

    Parameters
    ----------
    client
        Guarded client that runs every query.
    cohort
        Cohort definition.
    preset
        Concepts to use as state features.
    itemid_map
        Itemid map for features and medications. All of its itemids are
        validated.
    action_config
        Bins and windows for medication actions.

    Returns
    -------
    EHRDataset
        One trajectory per admission, with metadata ``died``,
        ``feature_names``, ``action_names``, ``action_sizes``, and
        ``provenance``.

    Raises
    ------
    EHRValidationError
        If the map's labels differ from MIMIC-IV or the preset names a missing
        concept.
    BudgetExceededError
        If any query's dry run exceeds the byte cap.
    BigQueryAuthError
        If any query fails.
    """

    resolved = preset.resolve(itemid_map)
    feature_entries = [entry for entries in resolved.values() for entry in entries]
    concept_by_itemid = _concept_by_itemid(resolved)
    input_entries = _entries_by_source(itemid_map, "inputevents")
    _validate_live_item_labels(client, itemid_map)

    admissions_result = client.query_dataframe(
        cohort.admissions_sql(),
        cache_key_parts=(itemid_map.version, preset.name, "admissions"),
    )
    query_results = [admissions_result]

    feature_frames = []
    vitals = _entries_by_source_from_entries(feature_entries, "chartevents")
    if vitals:
        result = client.query_dataframe(
            cohort.vitals_sql(entry.itemid for entry in vitals),
            cache_key_parts=(itemid_map.version, preset.name, "vitals"),
        )
        query_results.append(result)
        feature_frames.append(_canonicalize_events(result.dataframe, concept_by_itemid))
    labs = _entries_by_source_from_entries(feature_entries, "labevents")
    if labs:
        result = client.query_dataframe(
            cohort.labs_sql(entry.itemid for entry in labs),
            cache_key_parts=(itemid_map.version, preset.name, "labs"),
        )
        query_results.append(result)
        feature_frames.append(_canonicalize_events(result.dataframe, concept_by_itemid))

    if input_entries:
        inputevents_result = client.query_dataframe(
            cohort.inputevents_sql(entry.itemid for entry in input_entries),
            cache_key_parts=(itemid_map.version, preset.name, "inputevents"),
        )
        query_results.append(inputevents_result)
        inputevents = inputevents_result.dataframe
    else:
        inputevents = pd.DataFrame(
            columns=[
                "starttime",
                "endtime",
                "itemid",
                "rate",
                "rateuom",
                "patientweight",
                "amount",
                "statusdescription",
            ]
        )

    features = (
        pd.concat(feature_frames, ignore_index=True)
        if feature_frames
        else pd.DataFrame(
            columns=["subject_id", "hadm_id", "charttime", "feature", "valuenum"]
        )
    )
    ds = EHRDataset()
    ds.tables["admissions"] = admissions_result.dataframe
    ds.tables["features"] = features
    ds.tables["inputevents"] = inputevents
    ds.trajectories = build_state_matrix(ds.tables)

    # One record per load: every trajectory must share it, timestamp included.
    provenance = _provenance(
        query_results,
        itemid_map=itemid_map,
        preset=preset,
        cohort=cohort,
    )
    for trajectory in ds:
        trajectory.actions = build_medication_actions(
            _events_for_trajectory(inputevents, trajectory.subject_id, trajectory.admission_id),
            trajectory.timestamps,
            config=action_config,
        )
        trajectory.metadata["action_names"] = ["vasopressor_bin", "fluid_bin"]
        trajectory.metadata["action_sizes"] = [
            action_config.vasopressor_bins.n_bins,
            action_config.fluid_bins.n_bins,
        ]
        trajectory.metadata["provenance"] = dict(provenance)

    return ds


def _concept_by_itemid(
    resolved: dict[str, list[ItemIdEntry]],
) -> dict[int, str]:
    return {
        entry.itemid: concept
        for concept, entries in resolved.items()
        for entry in entries
    }


def _entries_by_source(itemid_map: ItemIdMap, source: str) -> list[ItemIdEntry]:
    entries = [entry for values in itemid_map.concepts.values() for entry in values]
    return _entries_by_source_from_entries(entries, source)


def _entries_by_source_from_entries(
    entries: list[ItemIdEntry],
    source: str,
) -> list[ItemIdEntry]:
    return [entry for entry in entries if entry.source == source]


def _canonicalize_events(
    events: pd.DataFrame,
    concept_by_itemid: dict[int, str],
) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(
            columns=["subject_id", "hadm_id", "charttime", "feature", "valuenum"]
        )
    df = events.copy()
    df["feature"] = df["itemid"].map(lambda itemid: concept_by_itemid[int(itemid)])
    return df[["subject_id", "hadm_id", "charttime", "feature", "valuenum"]]


def _events_for_trajectory(
    inputevents: pd.DataFrame,
    subject_id: str,
    admission_id: str,
) -> pd.DataFrame:
    if inputevents.empty or "subject_id" not in inputevents.columns:
        return inputevents
    return inputevents[
        (inputevents["subject_id"].astype(str) == subject_id)
        & (inputevents["hadm_id"].astype(str) == admission_id)
    ]


def _provenance(
    results: list[QueryResult],
    *,
    itemid_map: ItemIdMap,
    preset: FeaturePreset,
    cohort: BigQueryCohort,
) -> dict[str, object]:
    return {
        "bigquery_job_ids": [
            result.job_id for result in results if result.job_id is not None
        ],
        "query_hash": ":".join(result.query_hash for result in results),
        "itemid_map_version": itemid_map.version,
        "feature_preset": preset.name,
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "mimic_version": cohort.mimic_version.replace("_", "."),
    }


def _validate_live_item_labels(
    client: GuardedBigQueryClient,
    itemid_map: ItemIdMap,
) -> None:
    icu_itemids = [
        entry.itemid
        for entry in _entries_by_source(itemid_map, "chartevents")
        + _entries_by_source(itemid_map, "inputevents")
    ]
    lab_itemids = [entry.itemid for entry in _entries_by_source(itemid_map, "labevents")]
    labels = []
    if icu_itemids:
        labels.append(
            client.query_dataframe(
                _label_sql("physionet-data.mimiciv_3_1_icu.d_items", icu_itemids),
                cache_key_parts=(itemid_map.version, "icu_labels"),
            ).dataframe
        )
    if lab_itemids:
        labels.append(
            client.query_dataframe(
                _label_sql("physionet-data.mimiciv_3_1_hosp.d_labitems", lab_itemids),
                cache_key_parts=(itemid_map.version, "lab_labels"),
            ).dataframe
        )
    if labels:
        validate_itemid_map(itemid_map, pd.concat(labels, ignore_index=True))


def _label_sql(table: str, itemids: list[int]) -> str:
    itemid_sql = ", ".join(str(int(itemid)) for itemid in itemids)
    return f"""
SELECT itemid, label
FROM `{table}`
WHERE itemid IN ({itemid_sql})
ORDER BY itemid
"""
