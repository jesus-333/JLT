"""
Registry of registered ``autoresearch`` experiments.

While :mod:`~jlt.autoresearch.manage.experiments` orchestrates the high-level operations (add, list, remove) and :mod:`~jlt.autoresearch.manage.validation` checks that an experiment folder is well formed, this module manages *where* the registered experiments live on disk and how their metadata is read and written.

Registering an experiment does **not** copy the experiment files : only the path to the experiment folder (plus a bit of metadata) is saved internally.
For each experiment a small folder is created inside the JLT configuration directory.
This internal folder is meant to hold a backup of all the information produced by ``autoresearch`` (logs, results, ...), so that a copy survives even if the original experiment folder is lost.

Layout of the configuration directory ::

    <config_dir>/
        autoresearch/
            experiments/
                <experiment_name>/
                    info.json       ---> registry entry (path, metric, direction, ...)
                    summary_log.md  ---> backup of the per-experiment summary log
                    readme.md       ---> short description of the folder
                ...

The configuration directory (``<config_dir>``) is the very same one used by every other JLT tool, so :func:`~jlt.shared_knowledge.paths.get_config_dir` is reused here to keep a single source of truth for the JLT configuration root.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import shutil

# Specific imports
from pathlib import Path

# Internal imports
# The JLT configuration root and the toml/json IO helpers are generic and live
# directly under ``shared_knowledge`` (not inside any specific tool). Reusing
# them here keeps a single source of truth and avoids duplicating logic.
from jlt.shared_knowledge.config_io import read_config_file, write_config_file
from jlt.shared_knowledge.paths import get_config_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Name of the autoresearch sub-directory inside the JLT configuration directory.
AUTORESEARCH_DIR_NAME = "autoresearch"

# Name of the sub-directory holding one folder per registered experiment.
EXPERIMENTS_DIR_NAME = "experiments"

# Name of the file storing the metadata of a single experiment.
INFO_FILE_NAME = "info.json"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Path helpers

def get_autoresearch_dir() -> Path :
    """
    Return the autoresearch sub-directory inside the JLT configuration directory.

    Returns
    -------
    autoresearch_dir : pathlib.Path
        The (not necessarily existing) autoresearch directory.
    """

    return get_config_dir() / AUTORESEARCH_DIR_NAME

def get_experiments_dir() -> Path :
    """
    Return the directory holding one folder per registered experiment.
    """

    return get_autoresearch_dir() / EXPERIMENTS_DIR_NAME

def get_experiment_dir(experiment_name : str) -> Path :
    """
    Return the internal folder associated with a given experiment name.

    Parameters
    ----------
    experiment_name : str
        The name under which the experiment is (or will be) registered.

    Returns
    -------
    path : pathlib.Path
        Path to the ``<experiment_name>`` internal folder.
    """

    return get_experiments_dir() / experiment_name

def get_experiment_info_path(experiment_name : str) -> Path :
    """
    Return the path of the ``info.json`` file for a given experiment name.
    """

    return get_experiment_dir(experiment_name) / INFO_FILE_NAME

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Listing / existence

def list_experiments() -> list :
    """
    Return the sorted list of registered experiment names.

    Returns
    -------
    names : list
        The names of every registered experiment (empty if none).
    """

    experiments_dir = get_experiments_dir()

    if not experiments_dir.is_dir() :
        return []

    # A registered experiment is a sub-folder that contains an ``info.json``
    # file. Anything else found in the directory is ignored on purpose.
    return sorted(
        path.name
        for path in experiments_dir.iterdir()
        if (path / INFO_FILE_NAME).is_file()
    )

def experiment_exists(experiment_name : str) -> bool :
    """
    Return whether an experiment is already registered.

    Parameters
    ----------
    experiment_name : str
        The name to look up.

    Returns
    -------
    exists : bool
        ``True`` if the experiment is registered, ``False`` otherwise.
    """

    return get_experiment_info_path(experiment_name).is_file()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Metadata read / write

def read_experiment_info(experiment_name : str) -> dict :
    """
    Read the metadata of a registered experiment.

    Parameters
    ----------
    experiment_name : str
        The name of the experiment whose metadata is requested.

    Returns
    -------
    info : dict
        The metadata stored in the experiment ``info.json`` file.

    Raises
    ------
    ValueError
        If the experiment is not registered.
    """

    if not experiment_exists(experiment_name) :
        raise ValueError(f"Experiment '{experiment_name}' is not registered.")

    return read_config_file(get_experiment_info_path(experiment_name))

def save_experiment_info(experiment_name : str, info : dict) -> None :
    """
    Save (create or overwrite) the metadata of an experiment.

    The internal experiment folder is created if it does not exist yet.

    Parameters
    ----------
    experiment_name : str
        The name under which the experiment is registered.
    info : dict
        The metadata dictionary to store in ``info.json``.
    """

    # ``write_config_file`` already creates the parent directory if needed.
    write_config_file(get_experiment_info_path(experiment_name), info)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Removal

def remove_experiment(experiment_name : str) -> None :
    """
    Remove an experiment from the registry.

    Only the internal folder (the registry entry) is deleted : the original experiment folder and the ``jlt_log_<experiment_name>`` folder next to it are left untouched.

    Parameters
    ----------
    experiment_name : str
        The name of the experiment to remove. It must already be registered.

    Raises
    ------
    ValueError
        If ``experiment_name`` is not registered.
    """

    if not experiment_exists(experiment_name) :
        raise ValueError(f"Experiment '{experiment_name}' is not registered.")

    # Delete the whole internal folder (info.json, backup logs, ...). The user
    # owned experiment folder is intentionally left in place.
    shutil.rmtree(get_experiment_dir(experiment_name))
