"""
Synchronisation between an experiment log folder and the tool's internal backup.

Every registered experiment has its logs and results in **two** places (see :mod:`~jlt.autoresearch.manage.registry`) :

- the ``jlt_log_<name>`` folder created next to the experiment folder (the *external* copy),
- a ``<name>`` folder inside the JLT configuration directory (the *internal* backup).

This module copies the produced files from one side to the other.
By default it copies the external log folder into the internal backup (this is the very last step of every :func:`~jlt.autoresearch.run.runner.run_experiment` round).
With ``reverse = True`` it copies the internal backup back into the external folder, which is useful to restore the experiment files if the external folder is lost.

The synchronisation is **copy only** : it never deletes files at the destination, and it never touches the internal ``info.json`` registry entry (that file is metadata, not a log artifact).
It copies the whole log folder **recursively**, so the per-round ``round_<i>_backup`` sub-folders (each holding a round log and a copy of the config that produced it) are mirrored as well.
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

def _copy_log_files(source : Path, destination : Path, skip_info : bool = True) -> None :
    """
    Recursively copy the content of ``source`` into ``destination``.

    Files are copied and sub-folders are mirrored, so the per-round ``round_<i>_backup`` folders are synchronised together with the top-level cumulative files.
    The internal ``info.json`` registry entry is skipped at the top level so the registry metadata is never overwritten by a log synchronisation.
    Existing files at the destination are overwritten ; files only present at the destination are left untouched (the sync never deletes).

    Parameters
    ----------
    source : pathlib.Path
        The folder to copy the content from.
    destination : pathlib.Path
        The folder to copy the content into. It is created if missing.
    skip_info : bool, default True
        Whether to skip ``info.json`` at this level. It is ``True`` only for the top-level call (where the registry entry lives) and ``False`` while recursing, so a config file inside a backup sub-folder is never mistaken for the registry entry.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Make sure the destination exists

    destination.mkdir(parents = True, exist_ok = True)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Copy every entry (recursing into sub-folders)

    for item in source.iterdir() :

        # ``info.json`` is the registry entry, not a log artifact : never copy it
        # (only relevant at the top level, where the registry entry lives).
        if skip_info and item.name == registry.INFO_FILE_NAME :
            continue

        target = destination / item.name

        if item.is_dir() :
            # Mirror the sub-folder (e.g. a ``round_<i>_backup`` folder).
            _copy_log_files(item, target, skip_info = False)
        elif item.is_file() :
            # ``copy2`` preserves the file metadata (e.g. modification time).
            shutil.copy2(item, target)
