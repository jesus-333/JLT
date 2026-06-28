"""
Training and evaluation pipeline for the sklearn ``autoresearch`` example.

This is the part ``autoresearch`` ultimately cares about : given the two configurations (the common one and the one of the selected classifier) and the data, build a scikit-learn pipeline, fit it and return the metric to optimize (top-1 accuracy on the validation set).

The pipeline is :

1. an optional :class:`~sklearn.preprocessing.StandardScaler` (driven by the common ``standardize`` flag) ;
2. an optional :class:`~sklearn.decomposition.PCA` dimensionality reduction (driven by the common ``pca_components`` value, ``0`` to disable) ;
3. the classifier selected by the common ``classifier`` key, built from its own config file.

The first two steps are deliberately *common* hyperparameters : they apply to every classifier, which is exactly what the general config file is for.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import random

# Specific imports
import numpy as np
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Internal imports
from classifiers import build_classifier, validate_classifier_config

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Mandatory keys expected in the general (common) config file.
GENERAL_REQUIRED_KEYS = (
    "seed", "classifier", "train_samples_per_dataset", "val_samples_per_dataset",
    "standardize", "pca_components",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Configuration validation

def validate_general_config(general_config : dict) -> None :
    """
    Check that the general (common) configuration is internally consistent.

    Following the repository convention, any inconsistency raises an exception rather than being silently fixed.

    Parameters
    ----------
    general_config : dict
        The common configuration dictionary (from ``general.toml``).

    Raises
    ------
    KeyError
        If a mandatory key is missing.
    ValueError
        If a value is out of its valid range.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Mandatory keys

    for key in GENERAL_REQUIRED_KEYS :
        if key not in general_config :
            raise KeyError(f"Missing mandatory key '{key}' in the general config.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Ranges

    if general_config["train_samples_per_dataset"] <= 0 :
        raise ValueError(
            f"'train_samples_per_dataset' must be positive, got {general_config['train_samples_per_dataset']}."
        )

    if general_config["val_samples_per_dataset"] <= 0 :
        raise ValueError(
            f"'val_samples_per_dataset' must be positive, got {general_config['val_samples_per_dataset']}."
        )

    # ``pca_components`` is the number of PCA components, or 0 to disable PCA entirely.
    if general_config["pca_components"] < 0 :
        raise ValueError(
            f"'pca_components' must be >= 0 (0 disables PCA), got {general_config['pca_components']}."
        )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public function

def train_and_evaluate(
        general_config    : dict,
        classifier_name   : str,
        classifier_config : dict,
        x_train           : np.ndarray,
        y_train           : np.ndarray,
        x_val             : np.ndarray,
        y_val             : np.ndarray,
    ) -> float :
    """
    Build the pipeline, fit it on the training set and return its validation accuracy.

    Parameters
    ----------
    general_config : dict
        The common configuration (seed, preprocessing, which classifier to use).
    classifier_name : str
        The selected classifier name (the ``classifier`` value of ``general_config``).
    classifier_config : dict
        The hyperparameters of the selected classifier (from ``<classifier_name>.toml``).
    x_train : numpy.ndarray
        Training features of shape ``(n_train, n_features)``.
    y_train : numpy.ndarray
        Training integer labels of shape ``(n_train,)``.
    x_val : numpy.ndarray
        Validation features of shape ``(n_val, n_features)``.
    y_val : numpy.ndarray
        Validation integer labels of shape ``(n_val,)``.

    Returns
    -------
    accuracy : float
        Top-1 accuracy on the validation set, in ``[0, 1]``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Input checks and setup

    validate_general_config(general_config)
    validate_classifier_config(classifier_name, classifier_config)

    seed = general_config["seed"]
    set_seed(seed)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Assemble the pipeline (preprocessing + classifier)

    steps = []

    if general_config["standardize"] :
        steps.append(("scaler", StandardScaler()))

    if general_config["pca_components"] > 0 :
        # PCA cannot ask for more components than ``min(n_samples, n_features)`` ;
        # clamp so a too-large value in the config is forgiving rather than fatal.
        max_components = min(general_config["pca_components"], x_train.shape[0], x_train.shape[1])
        steps.append(("pca", PCA(n_components = max_components, random_state = seed)))

    steps.append(("classifier", build_classifier(classifier_name, classifier_config, seed)))

    pipeline = Pipeline(steps)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Fit and evaluate

    pipeline.fit(x_train, y_train)

    # ``score`` returns the mean accuracy on the given data, exactly the metric to optimize.
    accuracy = pipeline.score(x_val, y_val)

    return float(accuracy)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Reproducibility

def set_seed(seed : int) -> None :
    """
    Seed the ``random`` and ``numpy`` generators for reproducibility.

    The scikit-learn estimators receive the same seed through their ``random_state`` argument (see :mod:`classifiers`), so a re-run with the same configuration is reproducible.

    Parameters
    ----------
    seed : int
        The random seed to apply.
    """

    random.seed(seed)
    np.random.seed(seed)
