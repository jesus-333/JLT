"""
Registry operations for ``autoresearch`` experiments.

While :mod:`~jlt.autoresearch.run` is in charge of *executing* an experiment, this module manages the *set* of experiments the user has registered : adding a new one, listing the registered ones and removing one.

Registering an experiment does **not** copy its files : only the path to the experiment folder (plus a bit of metadata : the metric to optimise and the optimisation direction) is saved internally.

This module is the public entry point of the :mod:`~jlt.autoresearch.manage` subpackage : it orchestrates the lower-level helpers, namely :mod:`~jlt.autoresearch.manage.validation` (folder checks) and :mod:`~jlt.autoresearch.manage.registry` (on-disk storage).

An experiment is described by four pieces of information :

- ``path_folder`` : path to the experiment folder (mandatory),
- ``metric_name`` : name of the metric to optimise (mandatory),
- the optimisation direction : ``ascending`` to maximise the metric, ``descending`` to minimise it (mandatory, exactly one),
- ``experiment_name`` : the name under which the experiment is registered (optional, defaults to the folder name).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from pathlib import Path

# Internal imports
from . import registry
from .validation import validate_experiment_folder

# Reuse the shared toml/json reader for the optional ``--experiment_info_path``
# file (it accepts both formats, exactly what we need here).
from jlt.shared_knowledge.config_io import read_config_file

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Prefix of the log folder created next to the experiment folder.
LOG_FOLDER_PREFIX = "jlt_log_"

# Name of the per-experiment summary log file.
SUMMARY_LOG_FILE_NAME = "summary_log.md"

# Name of the readme file describing the log folder.
README_FILE_NAME = "readme.md"

# Name of the file that keeps track of how many rounds have been executed.
ROUND_FILE_NAME = "round.txt"

# Placeholder content of the summary log before any experiment has been run.
NO_EXPERIMENT_MESSAGE = "No experiment has been executed yet"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Add

def add_experiment(
    path_folder     : str | Path,
    metric_name     : str,
    ascending       : bool,
    experiment_name : str | None = None,
) -> str :
    """
    Register a new experiment in the ``autoresearch`` registry.

    Note that this function does **not** copy the experiment files : it only saves the path to the experiment folder (and a bit of metadata) internally.

    Parameters
    ----------
    path_folder : str or pathlib.Path
        Path to a valid experiment folder (see :func:`~jlt.autoresearch.manage.validation.validate_experiment_folder` for the requirements).
    metric_name : str
        Name of the metric to optimise.
    ascending : bool
        ``True`` to maximise the metric, ``False`` to minimise it.
    experiment_name : str, optional
        Name under which to register the experiment.
        If ``None`` (default) the name of the folder is used.

    Returns
    -------
    experiment_name : str
        The name under which the experiment has been registered.

    Raises
    ------
    FileNotFoundError
        If the experiment folder (or its mandatory content) is missing.
    ValueError
        If the experiment folder is invalid or an experiment with the same name is already registered.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Validate the experiment folder

    # Store an absolute path so the experiment can be found regardless of the
    # working directory from which ``autoresearch`` is later invoked.
    path_folder = Path(path_folder).expanduser().resolve()

    # Raises if the folder, the ``config`` sub-folder or ``run.py`` are missing
    # or if ``run.py`` does not expose a valid ``run`` function.
    validate_experiment_folder(path_folder)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Resolve the experiment name and guard against duplicates

    # Default the experiment name to the folder name when not provided.
    if experiment_name is None :
        experiment_name = path_folder.name

    if registry.experiment_exists(experiment_name) :
        raise ValueError(
            f"An experiment named '{experiment_name}' is already registered. "
            f"Remove it first with 'jlt autoresearch remove --experiment_name {experiment_name}'."
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the log folder next to the experiment folder

    # The log folder lives next to (i.e. as a sibling of) the experiment folder.
    log_folder = path_folder.parent / f"{LOG_FOLDER_PREFIX}{experiment_name}"
    _create_log_folder(log_folder, experiment_name)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Save the metadata (and a backup of the logs) inside the tool

    optimization_direction = "ascending" if ascending else "descending"

    info = {
        "experiment_name"        : experiment_name,
        "path_folder"            : str(path_folder),
        "metric_name"            : metric_name,
        "optimization_direction" : optimization_direction,
        "log_folder"             : str(log_folder),
    }

    registry.save_experiment_info(experiment_name, info)

    # Mirror the freshly created log files inside the tool's internal folder, so
    # a backup exists from the very beginning (see the module docstring of
    # :mod:`~jlt.autoresearch.manage.registry` for the rationale).
    _create_log_folder(registry.get_experiment_dir(experiment_name), experiment_name)

    return experiment_name

def add_experiment_from_info_file(experiment_info_path : str | Path) -> str :
    """
    Register a new experiment reading every field from a single ``json``/``toml`` file.

    The file must contain the same fields exposed as flags by the ``add`` subcommand :

    - ``path_folder`` (mandatory),
    - ``metric_name`` (mandatory),
    - exactly one of ``ascending`` / ``descending`` set to ``true`` (mandatory),
    - ``experiment_name`` (optional).

    Parameters
    ----------
    experiment_info_path : str or pathlib.Path
        Path to a ``json`` or ``toml`` file describing the experiment.

    Returns
    -------
    experiment_name : str
        The name under which the experiment has been registered.

    Raises
    ------
    ValueError
        If a mandatory field is missing or the optimisation direction is not specified exactly once.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Read and validate the fields

    info = read_config_file(experiment_info_path)

    path_folder = info.get("path_folder")
    if path_folder is None :
        raise ValueError(f"The info file '{experiment_info_path}' must contain a 'path_folder' field.")

    metric_name = info.get("metric_name")
    if metric_name is None :
        raise ValueError(f"The info file '{experiment_info_path}' must contain a 'metric_name' field.")

    ascending  = bool(info.get("ascending", False))
    descending = bool(info.get("descending", False))
    ascending  = _resolve_direction(ascending, descending)

    # The experiment name is optional : default it to ``None`` so that
    # ``add_experiment`` falls back to the folder name.
    experiment_name = info.get("experiment_name")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Delegate to the main add function

    return add_experiment(
        path_folder     = path_folder,
        metric_name     = metric_name,
        ascending       = ascending,
        experiment_name = experiment_name,
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# List / remove

def list_experiments() -> list :
    """
    Return the registered experiments.

    Returns
    -------
    experiments : list
        The names of every registered experiment (empty if none).
    """

    return registry.list_experiments()

def remove_experiment(experiment_name : str) -> None :
    """
    Remove an experiment from the ``autoresearch`` registry.

    Note that this only removes the experiment from the registry : the original experiment folder (and the ``jlt_log_<experiment_name>`` folder next to it) is **not** physically deleted.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment to remove. It must already be registered.

    Raises
    ------
    ValueError
        If ``experiment_name`` is not registered.
    """

    registry.remove_experiment(experiment_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _resolve_direction(ascending : bool, descending : bool) -> bool :
    """
    Turn the ``ascending`` / ``descending`` pair into a single boolean.

    Exactly one of the two must be ``True``.

    Parameters
    ----------
    ascending : bool
        Whether the metric should be maximised.
    descending : bool
        Whether the metric should be minimised.

    Returns
    -------
    ascending : bool
        ``True`` to maximise the metric, ``False`` to minimise it.

    Raises
    ------
    ValueError
        If both or neither of ``ascending`` / ``descending`` are set.
    """

    if ascending and descending :
        raise ValueError("'ascending' and 'descending' cannot be specified together.")

    if not ascending and not descending :
        raise ValueError("Exactly one of 'ascending' / 'descending' must be specified.")

    return ascending

def _create_log_folder(log_folder : Path, experiment_name : str) -> None :
    """
    Create a log folder and populate it with its initial files.

    The folder is created (if missing) together with :

    - a ``summary_log.md`` file (stating that no experiment has been run yet),
    - a ``readme.md`` file explaining the purpose of the folder,
    - a ``round.txt`` file holding the number of executed rounds (initially ``0``).

    Existing files are left untouched, so calling this on an already populated folder never discards previous content.

    Parameters
    ----------
    log_folder : pathlib.Path
        The folder to create and populate.
    experiment_name : str
        Name of the experiment the folder belongs to (used in the readme).
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the folder

    log_folder.mkdir(parents = True, exist_ok = True)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the summary log (only if it does not exist yet)

    summary_log = log_folder / SUMMARY_LOG_FILE_NAME
    if not summary_log.exists() :
        summary_log.write_text(f"{NO_EXPERIMENT_MESSAGE}\n", encoding = "utf-8")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the readme (only if it does not exist yet)

    readme = log_folder / README_FILE_NAME
    if not readme.exists() :
        readme.write_text(_build_readme_content(experiment_name), encoding = "utf-8")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the round counter (only if it does not exist yet)

    # The round counter starts at ``0`` : no round has been executed at
    # registration time. It is incremented by the ``run`` command at the end of
    # each round (see :mod:`~jlt.autoresearch.run.round_io`).
    round_file = log_folder / ROUND_FILE_NAME
    if not round_file.exists() :
        round_file.write_text("0\n", encoding = "utf-8")

def _build_readme_content(experiment_name : str) -> str :
    """
    Return the content of the readme placed inside a log folder.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment the folder belongs to.

    Returns
    -------
    content : str
        The markdown content of the readme.
    """

    return (
        f"# autoresearch logs : {experiment_name}\n"
        "\n"
        "This folder was automatically generated by the JLT `autoresearch` tool.\n"
        "\n"
        f"It stores the logs and results produced by `autoresearch` for the experiment "
        f"`{experiment_name}` : per-round logs, the metric values obtained at each round "
        "and a summary of the optimisation process (`summary_log.md`).\n"
        "\n"
        "A copy of this information is also kept inside the tool's own configuration "
        "directory, so that a backup survives if this folder is lost (and vice versa).\n"
    )
