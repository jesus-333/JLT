"""
Entry point for the scikit-learn ``autoresearch`` example experiment.

This experiment trains a **classic machine-learning classifier** (no neural network) on the same combined dataset as the neural-network example : FashionMNIST, KMNIST, EMNIST (``balanced`` split) and CIFAR10, harmonized to flattened grayscale 28x28 feature vectors and restricted to a fixed selection of 10 classes spanning all four datasets (re-mapped to ``0..9``).
The metric returned to ``autoresearch`` is the top-1 accuracy on the combined validation (test) set (maximize).

The experiment is driven by **several config files** living in ``config/`` :

- ``general.toml`` holds the hyperparameters common to every classifier (the seed, the data subsample sizes, the shared preprocessing and, crucially, the ``classifier`` key that selects WHICH algorithm to use this round) ;
- one ``<classifier>.toml`` per supported algorithm, holding all of that algorithm's hyperparameters.

``run`` reads ``general.toml``, loads the config file of the selected classifier, builds the data and delegates to the shared training pipeline.
This is exactly the multi-config-file scenario the example is meant to exercise : every round ``autoresearch`` may edit any of the config files, but only the selected classifier's file (plus the common one) affects the result.

``autoresearch`` calls :func:`run` with no arguments and with the working directory set to this folder ; ``run`` is the only thing it needs.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import sys

# Specific imports
from pathlib import Path

# Internal imports
# The shared code lives in the sibling ``common`` folder. It is added to
# ``sys.path`` here (at import time) so the modules below can be imported as
# top-level modules, exactly like the experiment folder itself is made
# importable by the autoresearch runner.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "common"))

import tomllib

from data import build_combined_dataset
from pipeline import train_and_evaluate

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Where the torchvision datasets are downloaded / cached.
DATA_ROOT = str(_HERE.parent / "data")

# EMNIST split used to define the label offsets (kept the same as the neural-network
# example so the global label ids below are stable).
EMNIST_SPLIT = "balanced"

# The 10 global labels kept for this experiment, deliberately spread across all
# four datasets so it stays a genuinely "combined" problem. With the EMNIST
# "balanced" offsets the global label space is :
#   FashionMNIST 0..9 | KMNIST 10..19 | EMNIST 20..66 | CIFAR10 67..76
# Selection (3 + 2 + 3 + 2) :
#   FashionMNIST classes 0,1,2  -> 0,1,2
#   KMNIST       classes 0,1    -> 10,11
#   EMNIST       classes 0,1,2  -> 20,21,22
#   CIFAR10      classes 0,1    -> 67,68
# These are re-mapped to 0..9 (sorted order) inside the data builder.
SELECTED_GLOBAL_LABELS = [0, 1, 2, 10, 11, 20, 21, 22, 67, 68]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Experiment entry point

def run() -> float :
    """
    Train the selected classifier on the combined dataset and return the validation accuracy.

    Returns
    -------
    accuracy : float
        Top-1 accuracy on the (subsampled) combined validation set, in ``[0, 1]``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Load the common config and the selected classifier config

    general_config    = _load_config("general.toml")
    classifier_name   = general_config["classifier"]
    classifier_config = _load_config(f"{classifier_name}.toml")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build the subsampled, 10-class combined dataset

    x_train, y_train, x_val, y_val, num_classes = build_combined_dataset(
        seed                      = general_config["seed"],
        data_root                 = DATA_ROOT,
        emnist_split              = EMNIST_SPLIT,
        train_samples_per_dataset = general_config["train_samples_per_dataset"],
        val_samples_per_dataset   = general_config["val_samples_per_dataset"],
        selected_global_labels    = SELECTED_GLOBAL_LABELS,
    )

    print(f"Sklearn experiment : classifier '{classifier_name}', "
          f"{num_classes} classes, {x_train.shape[0]} train / {x_val.shape[0]} val samples.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Train and return the metric

    return train_and_evaluate(
        general_config    = general_config,
        classifier_name   = classifier_name,
        classifier_config = classifier_config,
        x_train           = x_train,
        y_train           = y_train,
        x_val             = x_val,
        y_val             = y_val,
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _load_config(file_name : str) -> dict :
    """
    Read one of this experiment's ``config`` files into a dictionary.

    Parameters
    ----------
    file_name : str
        Name of the file inside the ``config`` folder (e.g. ``"general.toml"``).

    Returns
    -------
    config : dict
        The parsed configuration.

    Raises
    ------
    FileNotFoundError
        If the requested config file does not exist (e.g. the ``classifier`` key names an algorithm without a matching config file).
    """

    config_path = _HERE / "config" / file_name

    if not config_path.is_file() :
        raise FileNotFoundError(
            f"Config file '{file_name}' not found in {config_path.parent}. "
            f"Make sure the 'classifier' value in general.toml matches an existing '<classifier>.toml' file."
        )

    with config_path.open("rb") as file_handle :
        return tomllib.load(file_handle)
