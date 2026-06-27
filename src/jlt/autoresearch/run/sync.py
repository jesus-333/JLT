"""
Synchronisation between an experiment log folder and the tool's internal backup.

Every registered experiment has its logs and results in **two** places (see :mod:`~jlt.autoresearch.manage.registry`) :

- the ``jlt_log_<name>`` folder created next to the experiment folder (the *external* copy),
- a ``<name>`` folder inside the JLT configuration directory (the *internal* backup).

This module copies the produced files from one side to the other.
By default it copies the external log folder into the internal backup (this is the very last step of every :func:`~jlt.autoresearch.run.runner.run_experiment` round).
With ``reverse = True`` it copies the internal backup back into the external folder, which is useful to restore the experiment files if the external folder is lost.

The synchronisation is **copy only** : it never deletes files at the destination, and it never touches the internal ``info.json`` registry entry (that file is metadata, not a log artifact).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import shutil

# Specific imports
from pathlib import Path

# Internal imports
from ..manage import registry

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public function

def sync_experiment(experiment_name : str | None = None, reverse : bool = False) -> None :
    """
    Synchronise an experiment log folder with its internal backup.

    Parameters
    ----------
    experiment_name : str, optional
        Name under which the experiment is registered.
        If ``None`` (default) the name of the current working directory is used (matching the convention that an experiment defaults to its folder name).
    reverse : bool, default False
        If ``False`` (default) the external ``jlt_log_<name>`` folder is copied into the internal backup.
        If ``True`` the direction is reversed : the internal backup is copied into the external folder.

    Raises
    ------
    ValueError
        If ``experiment_name`` is not registered.
    FileNotFoundError
        If the source folder of the chosen direction does not exist.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Resolve the experiment name

    # When no name is given, fall back to the current folder name : this mirrors
    # the default used by ``add`` (the experiment defaults to its folder name).
    if experiment_name is None :
        experiment_name = Path.cwd().name

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Resolve the two endpoints from the registry

    # ``read_experiment_info`` already raises a clear error if the experiment is
    # not registered.
    info = registry.read_experiment_info(experiment_name)

    external_folder = Path(info["log_folder"])
    internal_folder = registry.get_experiment_dir(experiment_name)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Pick the direction and copy

    if reverse :
        source, destination = internal_folder, external_folder
    else :
        source, destination = external_folder, internal_folder

    if not source.is_dir() :
        raise FileNotFoundError(f"Source folder to synchronise does not exist : {source}")

    _copy_log_files(source, destination)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _copy_log_files(source : Path, destination : Path) -> None :
    """
    Copy every log file from ``source`` to ``destination``.

    The copy is shallow on purpose (the log folders only contain files, no sub-folders) and skips the internal ``info.json`` registry entry so the registry metadata is never overwritten by a log synchronisation.
    Existing files at the destination are overwritten ; files only present at the destination are left untouched (the sync never deletes).

    Parameters
    ----------
    source : pathlib.Path
        The folder to copy the files from.
    destination : pathlib.Path
        The folder to copy the files into. It is created if missing.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Make sure the destination exists

    destination.mkdir(parents = True, exist_ok = True)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Copy every file (skipping the registry metadata)

    for item in source.iterdir() :

        # Only files are expected in a log folder ; ignore anything else (e.g. a
        # stray sub-folder) to keep the operation simple and predictable.
        if not item.is_file() :
            continue

        # ``info.json`` is the registry entry, not a log artifact : never copy it
        # so the registry metadata is preserved on both sides.
        if item.name == registry.INFO_FILE_NAME :
            continue

        # ``copy2`` preserves the file metadata (e.g. modification time).
        shutil.copy2(item, destination / item.name)
