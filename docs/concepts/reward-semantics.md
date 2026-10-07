# Reward semantics

A reward function decides what the learned policy is optimizing for. In
offline RL from health records, that choice carries most of the clinical
meaning of a study, so `ehr2rl` keeps rewards separate from data loading and
makes every reward swappable.

## When rewards are computed

Loading never sets rewards. Every loader returns trajectories with all-zero
rewards, and you apply a reward explicitly with
{py:meth}`~ehr2rl.reward.BaseReward.shape`. The same dataset can therefore be
shaped with several rewards and compared, without reloading.

## Terminal and dense rewards

| Kind | Placement | Built-in examples |
|---|---|---|
| Terminal | One value at the end of the episode, zero elsewhere | {py:class}`~ehr2rl.MortalityReward`, {py:class}`~ehr2rl.ReadmissionReward` |
| Dense | A value at each step from changes in state | {py:class}`~ehr2rl.SofaReward` |

Terminal rewards express the outcome directly but give a learning algorithm
little signal about which steps mattered. Dense rewards give per-step signal
but encode a judgement that the intermediate measure, such as SOFA score,
tracks the outcome you care about. {py:class}`~ehr2rl.CompositeReward` combines
both; the weights decide how much each matters.

## Where outcome information comes from

Rewards read trajectory metadata. The data source determines which rewards
are available without extra work:

| Reward | Needs | BigQuery | Synthetic |
|---|---|---|---|
| `MortalityReward` | `died` | Yes | Yes |
| `SofaReward` | `sofa_scores`, shape `(T,)` | **No** | Yes |
| `ReadmissionReward` | `readmitted_within_30_days` | **No** | **No** |

Computing SOFA scores or readmission outcomes from MIMIC-IV is a research
choice in its own right, with decisions about missing components and follow-up
windows. Add the result to each trajectory's `metadata` before shaping.

## Responsibility

`ehr2rl` implements common reward definitions from the offline RL literature.
It does not establish that any reward is clinically appropriate for a
question. In particular:

- rewards from mortality treat every death as equally bad and every survival as
  equally good, regardless of quality of life or cause;
- a policy that optimizes a proxy such as SOFA can learn to improve the proxy
  without improving outcomes;
- censored outcomes need an explicit decision. The default `NaN` for censored
  readmission is deliberately unusable for training so the decision cannot be
  skipped by accident.

Write down the reward you chose and why, alongside the dataset's
[provenance](provenance.md).

## Custom rewards

Any class that implements {py:meth}`~ehr2rl.reward.BaseReward.compute`,
returning an array of shape `(T,)` for one trajectory, works everywhere a
built-in reward does. See [Writing your own reward](../use/rewards.md#writing-your-own-reward).
