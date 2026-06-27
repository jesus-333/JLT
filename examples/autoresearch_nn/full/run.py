"""
Entry point for the *full* example experiment.

This experiment trains the configurable network on the **full** combination of FashionMNIST, KMNIST, EMNIST (``balanced`` split) and CIFAR10, keeping **every** class : ``10 + 10 + 47 + 10 = 77`` classes in total.
The metric returned to ``autoresearch`` is the top-1 accuracy on the combined validation (test) set.

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

from data import build_combined_loaders
from training import train_and_evaluate

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Where the torchvision datasets are downloaded / cached (shared by both experiments).
DATA_ROOT = str(_HERE.parent / "data")

# EMNIST split used for the full experiment : "balanced" keeps all 47 classes.
EMNIST_SPLIT = "balanced"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Experiment entry point

def run() -> float :
    """
    Train on the full combined dataset and return the validation accuracy.

    Returns
    -------
    accuracy : float
        Top-1 accuracy on the combined validation set, in ``[0, 1]``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Load the configuration

    config = _load_config()

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build the full combined data loaders (every class, every sample)

    train_loader, val_loader, num_classes = build_combined_loaders(
        batch_size             = config["batch_size"],
        seed                   = config["seed"],
        data_root              = DATA_ROOT,
        emnist_split           = EMNIST_SPLIT,
        subset_per_dataset     = None,
        selected_global_labels = None,
    )

    print(f"Full experiment : {num_classes} classes.")

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
