"""
Entry point for the *subset* example experiment.

This is the fast variant : it trains on a **small, deterministic subsample** of the four datasets, restricted to a **fixed selection of 10 classes spanning all four datasets** (re-mapped to ``0..9``).
A round therefore finishes in a couple of minutes, well under the 10-minute budget, which makes it the convenient one to iterate on with ``autoresearch``.
The metric returned is the top-1 accuracy on the (subsampled) combined validation set.

``autoresearch`` calls :func:`run` with no arguments and with the working directory set to this folder.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import sys

# Specific imports
from pathlib import Path

# Internal imports
# Add the sibling ``common`` folder to ``sys.path`` (at import time) so the shared
# modules can be imported as top-level modules.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "common"))

import tomllib

from data import build_combined_loaders
from training import train_and_evaluate

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Where the torchvision datasets are downloaded / cached (shared by both experiments).
DATA_ROOT = str(_HERE.parent / "data")

# EMNIST split used to define the label offsets (kept the same as the full
# experiment so the global label ids below are stable).
EMNIST_SPLIT = "balanced"

# Maximum number of samples kept from each dataset's train / test split.
SUBSET_TRAIN_PER_DATASET = 3000
SUBSET_VAL_PER_DATASET   = 1000

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
    Train on the subsampled 10-class dataset and return the validation accuracy.

    Returns
    -------
    accuracy : float
        Top-1 accuracy on the (subsampled) combined validation set, in ``[0, 1]``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Load the configuration

    config = _load_config()

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build the subsampled, 10-class data loaders

    train_loader, val_loader, num_classes = build_combined_loaders(
        batch_size             = config["batch_size"],
        seed                   = config["seed"],
        data_root              = DATA_ROOT,
        emnist_split           = EMNIST_SPLIT,
        subset_per_dataset     = (SUBSET_TRAIN_PER_DATASET, SUBSET_VAL_PER_DATASET),
        selected_global_labels = SELECTED_GLOBAL_LABELS,
    )

    print(f"Subset experiment : {num_classes} classes, "
          f"<= {SUBSET_TRAIN_PER_DATASET} train / {SUBSET_VAL_PER_DATASET} val samples per dataset.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Train and return the metric

    return train_and_evaluate(config, train_loader, val_loader, num_classes)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _load_config() -> dict :
    """
    Read this experiment's ``config/config.toml`` into a dictionary.

    Returns
    -------
    config : dict
        The experiment configuration.
    """

    config_path = _HERE / "config" / "config.toml"
    with config_path.open("rb") as file_handle :
        return tomllib.load(file_handle)
