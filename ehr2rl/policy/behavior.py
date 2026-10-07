"""Simple behavior policy estimator."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import KBinsDiscretizer, StandardScaler

from ehr2rl.data.dataset import EHRDataset


class BehaviorPolicy:
    """Estimate the probability of each observed action given the state.

    Only the first action column is modeled. Integer actions with at most
    ``n_action_bins`` distinct values are used as classes directly; other
    actions are split into at most ``n_action_bins`` quantile bins.

    Parameters
    ----------
    n_action_bins
        Maximum number of action classes.
    random_state
        Seed for the classifier.
    """

    def __init__(self, n_action_bins: int = 5, random_state: int = 42) -> None:
        self.n_action_bins = n_action_bins
        self.random_state = random_state
        self.discretizer: KBinsDiscretizer | None = None
        self.model: Any | None = None

    def fit(self, dataset: EHRDataset) -> BehaviorPolicy:
        """Fit the policy on every timestep of a dataset.

        Trains a standardized multinomial logistic regression, or a constant
        classifier when only one action class is observed.

        Parameters
        ----------
        dataset
            Non-empty dataset.

        Returns
        -------
        BehaviorPolicy
            This policy, for chaining.

        Raises
        ------
        ValueError
            If the dataset is empty.
        """
        states, actions = self._stack(dataset)
        labels = self._labels_from_actions(actions, fit=True)

        if np.unique(labels).shape[0] == 1:
            model = DummyClassifier(strategy="most_frequent")
        else:
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=2000,
                    random_state=self.random_state,
                ),
            )
        model.fit(states, labels)
        self.model = model
        return self

    def predict_proba(self, states: np.ndarray) -> np.ndarray:
        """Return the probability of each action class for each state.

        Parameters
        ----------
        states
            Shape ``(N, D)``.

        Returns
        -------
        numpy.ndarray
            Shape ``(N, n_classes)``. Columns follow ``model.classes_``.

        Raises
        ------
        ValueError
            If the policy has not been fit.
        """
        if self.model is None:
            raise ValueError("BehaviorPolicy must be fit before predict_proba().")
        return self.model.predict_proba(np.asarray(states, dtype=float))

    def propensity_scores(self, dataset: EHRDataset) -> np.ndarray:
        """Return the probability of the action actually taken at each timestep.

        An action class not seen during `fit` gets the first class's
        probability.

        Parameters
        ----------
        dataset
            Dataset to score, with the same action encoding used for fitting.

        Returns
        -------
        numpy.ndarray
            Shape ``(N,)``, where ``N`` is the total number of timesteps.

        Raises
        ------
        ValueError
            If the policy has not been fit or the dataset is empty.
        """
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
