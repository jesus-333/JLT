"""
Factories and validation for the scikit-learn classifiers of the example.

This module turns the plain strings / numbers found in each classifier's configuration file into the corresponding scikit-learn estimator.
Every supported algorithm has :

- an entry in :data:`CLASSIFIER_BUILDERS` (the name -> builder mapping), and
- a matching ``<name>.toml`` file in the experiment ``config`` folder holding *all* of its hyperparameters.

The name used in the general config (the ``classifier`` key) is exactly the key of :data:`CLASSIFIER_BUILDERS` and the basename of the per-algorithm config file, so adding a new algorithm is "add a builder here + drop a ``<name>.toml`` next to the others".

Keeping every "string -> estimator" mapping here (instead of scattering ``if name == ...`` checks across the pipeline) gives a single place to extend and a single place to validate.

A couple of conventions make the hyperparameters expressible in plain TOML (which has no ``null``) :

- an integer hyperparameter that scikit-learn accepts as ``None`` to mean "no limit" (e.g. ``max_depth``) is written as ``0`` in the config and converted to ``None`` here ;
- a ``max_features`` value of ``"all"`` is converted to ``None`` (scikit-learn's "use every feature", for the tree-based estimators).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Builders

def build_logistic_regression(config : dict, seed : int) -> LogisticRegression :
    """
    Build a :class:`~sklearn.linear_model.LogisticRegression` from its config.
    """

    return LogisticRegression(
        C            = config["C"],
        max_iter     = config["max_iter"],
        solver       = config["solver"],
        tol          = config["tol"],
        random_state = seed,
    )

def build_random_forest(config : dict, seed : int) -> RandomForestClassifier :
    """
    Build a :class:`~sklearn.ensemble.RandomForestClassifier` from its config.
    """

    return RandomForestClassifier(
        n_estimators      = config["n_estimators"],
        max_depth         = _none_if_zero(config["max_depth"]),
        min_samples_split = config["min_samples_split"],
        min_samples_leaf  = config["min_samples_leaf"],
        max_features      = _max_features(config["max_features"]),
        criterion         = config["criterion"],
        random_state      = seed,
        n_jobs            = -1,
    )

def build_svm(config : dict, seed : int) -> SVC :
    """
    Build a :class:`~sklearn.svm.SVC` from its config.
    """

    return SVC(
        C            = config["C"],
        kernel       = config["kernel"],
        gamma        = config["gamma"],
        degree       = config["degree"],
        random_state = seed,
    )

def build_knn(config : dict, seed : int) -> KNeighborsClassifier :
    """
    Build a :class:`~sklearn.neighbors.KNeighborsClassifier` from its config.

    ``KNeighborsClassifier`` has no randomness, so ``seed`` is accepted (for a uniform builder signature) but unused.
    """

    return KNeighborsClassifier(
        n_neighbors = config["n_neighbors"],
        weights     = config["weights"],
        p           = config["p"],
        algorithm   = config["algorithm"],
        n_jobs      = -1,
    )

def build_decision_tree(config : dict, seed : int) -> DecisionTreeClassifier :
    """
    Build a :class:`~sklearn.tree.DecisionTreeClassifier` from its config.
    """

    return DecisionTreeClassifier(
        max_depth         = _none_if_zero(config["max_depth"]),
        min_samples_split = config["min_samples_split"],
        min_samples_leaf  = config["min_samples_leaf"],
        criterion         = config["criterion"],
        max_features      = _max_features(config["max_features"]),
        random_state      = seed,
    )

def build_gradient_boosting(config : dict, seed : int) -> GradientBoostingClassifier :
    """
    Build a :class:`~sklearn.ensemble.GradientBoostingClassifier` from its config.
    """

    return GradientBoostingClassifier(
        n_estimators      = config["n_estimators"],
        learning_rate     = config["learning_rate"],
        max_depth         = config["max_depth"],
        min_samples_split = config["min_samples_split"],
        subsample         = config["subsample"],
        random_state      = seed,
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Registry

# Maps each classifier name (also the basename of its config file) to its builder.
# Adding a new algorithm is a one-line change here plus a matching ``<name>.toml``.
CLASSIFIER_BUILDERS = {
    "logistic_regression" : build_logistic_regression,
    "random_forest"       : build_random_forest,
    "svm"                 : build_svm,
    "knn"                 : build_knn,
    "decision_tree"       : build_decision_tree,
    "gradient_boosting"   : build_gradient_boosting,
}

# The mandatory keys expected in each classifier's config file. They mirror the
# keys read by the builders above and are used by :func:`validate_classifier_config`.
CLASSIFIER_REQUIRED_KEYS = {
    "logistic_regression" : ("C", "max_iter", "solver", "tol"),
    "random_forest"       : ("n_estimators", "max_depth", "min_samples_split", "min_samples_leaf", "max_features", "criterion"),
    "svm"                 : ("C", "kernel", "gamma", "degree"),
    "knn"                 : ("n_neighbors", "weights", "p", "algorithm"),
    "decision_tree"       : ("max_depth", "min_samples_split", "min_samples_leaf", "criterion", "max_features"),
    "gradient_boosting"   : ("n_estimators", "learning_rate", "max_depth", "min_samples_split", "subsample"),
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public functions

def build_classifier(name : str, config : dict, seed : int) :
    """
    Build the scikit-learn estimator selected by ``name`` from its config.

    Parameters
    ----------
    name : str
        One of the keys of :data:`CLASSIFIER_BUILDERS` (the ``classifier`` value of the general config).
    config : dict
        The hyperparameters read from the ``<name>.toml`` config file.
    seed : int
        Random seed forwarded to the estimator (ignored by estimators without randomness).

    Returns
    -------
    estimator : sklearn.base.BaseEstimator
        The configured, not-yet-fitted classifier.

    Raises
    ------
    ValueError
        If ``name`` is not a known classifier.
    """

    if name not in CLASSIFIER_BUILDERS :
        raise ValueError(
            f"Unknown classifier '{name}'. Expected one of {sorted(CLASSIFIER_BUILDERS)}."
        )

    return CLASSIFIER_BUILDERS[name](config, seed)

def validate_classifier_config(name : str, config : dict) -> None :
    """
    Check that a classifier name is known and its config holds every mandatory key.

    Following the repository convention, any inconsistency raises an exception rather than being silently fixed.

    Parameters
    ----------
    name : str
        The classifier name (the ``classifier`` value of the general config).
    config : dict
        The hyperparameters read from the ``<name>.toml`` config file.

    Raises
    ------
    ValueError
        If ``name`` is not a known classifier.
    KeyError
        If a mandatory hyperparameter is missing from ``config``.
    """

    if name not in CLASSIFIER_BUILDERS :
        raise ValueError(
            f"Unknown classifier '{name}'. Expected one of {sorted(CLASSIFIER_BUILDERS)}."
        )

    for key in CLASSIFIER_REQUIRED_KEYS[name] :
        if key not in config :
            raise KeyError(f"Missing mandatory key '{key}' in the '{name}' classifier config.")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _none_if_zero(value : int) :
    """
    Return ``None`` when ``value`` is ``0``, otherwise ``value`` itself.

    Used for integer hyperparameters (e.g. ``max_depth``) where scikit-learn uses ``None`` to mean "no limit", which TOML cannot represent directly.
    """

    return None if value == 0 else value

def _max_features(value : str) :
    """
    Translate a ``max_features`` config value into what scikit-learn expects.

    ``"all"`` becomes ``None`` (use every feature) ; ``"sqrt"`` / ``"log2"`` are passed through unchanged.

    Parameters
    ----------
    value : str
        The ``max_features`` value from the config (``"all"`` / ``"sqrt"`` / ``"log2"``).

    Returns
    -------
    max_features : str or None
        The value scikit-learn understands.
    """

    return None if value == "all" else value
