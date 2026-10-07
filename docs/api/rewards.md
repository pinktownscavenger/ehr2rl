# Rewards

See [Rewards](../use/rewards.md) for the metadata each reward needs and how to
write your own.

```{eval-rst}
.. autoclass:: ehr2rl.reward.BaseReward
   :members: compute, shape
```

```{eval-rst}
.. autoclass:: ehr2rl.MortalityReward
   :members: compute
```

```{eval-rst}
.. autoclass:: ehr2rl.SofaReward
   :members: compute
```

```{eval-rst}
.. autoclass:: ehr2rl.ReadmissionReward
   :members: compute
```

```{eval-rst}
.. autoclass:: ehr2rl.CompositeReward
   :members: compute
```
