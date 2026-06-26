"""
Registry operations for ``autoresearch`` experiments.

While :mod:`~jlt.autoresearch.run` is in charge of *executing* an experiment, this module manages the *set* of experiments the user has registered: adding a new one, listing the registered ones and removing one.

Registering an experiment does **not** copy its files: only the path to the experiment config folder is saved internally.

.. note::
    For now these functions are only stubs.
    The current implementation scope covers the CLI structure (subcommand parsing and dispatch wiring) only; the internal logic will be implemented in a later iteration.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from pathlib import Path

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Experiment management functions

def add_experiment(path_folder : str | Path, experiment_name : str | None = None) -> None :
    """
    Register a new experiment in the ``autoresearch`` registry.

    Note that this function does **not** copy the experiment files : it only saves the path to the experiment config folder internally.

    Parameters
    ----------
    path_folder : str or pathlib.Path
        Path to a valid experiment config folder.
    experiment_name : str, optional
        Name under which to register the experiment.
        If ``None`` (default) the name of the folder is used.

    Raises
    ------
    NotImplementedError
        Always, until the internal logic is implemented.
    """

    raise NotImplementedError("'autoresearch add' is not implemented yet.")

def list_experiments() -> list :
    """
    Return the registered experiments.

    Returns
    -------
    experiments : list
        The names of every registered experiment (empty if none).

    Raises
    ------
    NotImplementedError
        Always, until the internal logic is implemented.
    """

    raise NotImplementedError("'autoresearch list' is not implemented yet.")

def remove_experiment(experiment_name : str) -> None :
    """
    Remove an experiment from the ``autoresearch`` registry.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment to remove.

    Raises
    ------
    NotImplementedError
        Always, until the internal logic is implemented.
    """

    raise NotImplementedError("'autoresearch remove' is not implemented yet.")
