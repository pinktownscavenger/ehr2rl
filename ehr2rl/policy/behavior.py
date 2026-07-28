"""Simple behavior policy estimator."""

from __future__ import annotations

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import KBinsDiscretizer

from ehr2rl.data.dataset import EHRDataset


class BehaviorPolicy:
    """Estimate observed action probabilities from states."""

    def __init__(self, n_action_bins: int = 5, random_state: int = 42) -> None:
        # TODO(v0.2): replace placeholder actions with real medication actions.
        self.n_action_bins = n_action_bins
        self.random_state = random_state
        self.discretizer: KBinsDiscretizer | None = None
        self.model: LogisticRegression | DummyClassifier | None = None

    def fit(self, dataset: EHRDataset) -> BehaviorPolicy:
        states, actions = self._stack(dataset)
        labels = self._labels_from_actions(actions, fit=True)

        if np.unique(labels).shape[0] == 1:
            model: LogisticRegression | DummyClassifier = DummyClassifier(
                strategy="most_frequent"
            )
        else:
            model = LogisticRegression(
                max_iter=1000,
                random_state=self.random_state,
            )
        model.fit(states, labels)
        self.model = model
        return self

    def predict_proba(self, states: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ValueError("BehaviorPolicy must be fit before predict_proba().")
        return self.model.predict_proba(np.asarray(states, dtype=float))

    def propensity_scores(self, dataset: EHRDataset) -> np.ndarray:
        if self.model is None:
            raise ValueError("BehaviorPolicy must be fit before propensity_scores().")
        states, actions = self._stack(dataset)
        labels = self._labels_from_actions(actions, fit=False)
        probabilities = self.predict_proba(states)
        class_to_column = {label: i for i, label in enumerate(self.model.classes_)}
        scores = np.empty(labels.shape[0], dtype=float)
        for i, label in enumerate(labels):
            scores[i] = probabilities[i, class_to_column.get(label, 0)]
        return scores

    def _stack(self, dataset: EHRDataset) -> tuple[np.ndarray, np.ndarray]:
        if len(dataset) == 0:
            raise ValueError("BehaviorPolicy requires at least one trajectory.")
        states = np.vstack([trajectory.states for trajectory in dataset])
        actions = np.vstack([trajectory.actions for trajectory in dataset])
        return states, actions

    def _labels_from_actions(self, actions: np.ndarray, fit: bool) -> np.ndarray:
        primary = np.asarray(actions[:, 0], dtype=float).reshape(-1, 1)
        unique_values = np.unique(primary)
        if unique_values.shape[0] <= self.n_action_bins and np.allclose(
            primary, np.round(primary)
        ):
            return primary.astype(int).ravel()

        if fit:
            bins = min(self.n_action_bins, unique_values.shape[0])
            self.discretizer = KBinsDiscretizer(
                n_bins=bins,
                encode="ordinal",
                strategy="quantile",
                subsample=None,
            )
            return self.discretizer.fit_transform(primary).astype(int).ravel()

        if self.discretizer is None:
            raise ValueError("Continuous actions require a fitted discretizer.")
        return self.discretizer.transform(primary).astype(int).ravel()
