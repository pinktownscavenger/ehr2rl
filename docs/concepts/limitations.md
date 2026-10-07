# Limitations

:::{important}
`ehr2rl` is research infrastructure. It is not clinical decision support, does
not validate treatment recommendations, and does not define clinically valid
rewards. Policies trained on its datasets must not be used to guide patient
care. Responsibility for study design, reward choice, and interpretation rests
with the researcher.
:::

## Data access

- `ehr2rl` does not ship, mirror, or provide access to MIMIC-IV. Obtain data
  only through credentialed channels such as
  [PhysioNet](https://physionet.org/content/mimiciv/), and follow the data use
  agreement, including its rules on sharing derived data.
- Cached query results in `cache_dir` are MIMIC-IV data. Store and delete them
  under the same rules as the source data, and keep them out of version
  control.

## BigQuery workflow

- **Cost.** `maximum_bytes_billed` caps each query separately. One load runs up
  to six queries, so its worst-case cost is six times the cap.
- **Cohort selection.** The cohort is the first N ICU stays by identifier, not
  a random or representative sample.
- **Admissions, not stays.** Trajectories are per hospital admission; several
  ICU stays in one admission are merged.
- **Irregular timesteps.** States use each distinct chart time. The preset's
  `aggregation` setting is not applied.
- **Units.** Features are not unit-converted. `temperature_f` and
  `temperature_c` are separate columns, and an itemid map's `conversion`
  field is informational only.
- **Missing values.** Gaps are forward-filled, and values before a feature's
  first measurement are `0.0`, which is not clinically meaningful.
- **Outcomes.** Only in-hospital mortality is extracted. SOFA scores and
  readmission outcomes must be computed separately.
- **Fluids.** Only two fluid itemids (NaCl 0.9% and Dextrose 5%) count toward
  fluid actions.
- **Errors.** `BigQueryAuthError` is raised for every query failure, not only
  authentication problems.
- Only MIMIC-IV v3.1 is supported.

## Actions and policy

- Norepinephrine-equivalent factors follow a common research convention and
  are not a clinical standard. Vasopressor rows with unrecognized rate units
  stop the load.
- {py:class}`~ehr2rl.BehaviorPolicy` models only the first action column unless
  you combine columns yourself, and its propensities for the training data are
  in-sample.

## Rewards

- {py:class}`~ehr2rl.ReadmissionReward` uses `NaN` for censored follow-up by
  default, and its `window_days` argument is not used.
- The `policy` argument of {py:meth}`~ehr2rl.reward.BaseReward.shape` is
  ignored by every built-in reward.

## Local CSV path

The [local CSV path](../use/local-csv.md) is frozen at its v0.1 behavior: raw
itemid features, labs not resampled, and placeholder all-zero actions. It
receives no itemid maps, presets, or validation.

## Synthetic data

Synthetic trajectories have plausible value ranges but no clinical structure:
actions follow a fixed rule, and mortality is random. Use them to develop and
test code, never to draw conclusions.

## Dependencies and stability

- `ehr2rl` is alpha software. Public APIs may change between minor versions;
  check the changelog when upgrading.
- `d3rlpy` may print deprecation warnings from its own dependencies, such as a
  notice that `gym` is unmaintained. These come from `d3rlpy`, not `ehr2rl`.
