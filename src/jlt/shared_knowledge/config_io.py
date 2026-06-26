"""
Reading and writing helpers for JLT configuration files.

Several JLT tools accept configuration as a plain Python dictionary.  On disk that dictionary can live in different formats : at the moment ``toml`` and ``json`` are supported. 
This module isolates the format specific logic so the rest of the code only ever deals with dictionaries.

It lives directly under :mod:`jlt.shared_knowledge` (rather than inside a specific tool) because it is generic and reused across tools, e.g. by the backend subsystem and by :mod:`~jlt.autoresearch`.

New formats can be added by extending :data:`READERS` (for parsing) and, if the format should also be writable, :data:`WRITERS`.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import json
import tomllib

# Specific imports
from pathlib import Path

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Format readers

def _read_json(path : Path) -> dict :
    """
    Read a ``json`` file and return its content as a dictionary.
    """

    with path.open("r", encoding = "utf-8") as file_handle :
        return json.load(file_handle)

def _read_toml(path : Path) -> dict :
    """
    Read a ``toml`` file and return its content as a dictionary.
    """

    # Note that ``tomllib`` requires the file to be opened in binary mode.
    with path.open("rb") as file_handle :
        return tomllib.load(file_handle)

# Map each supported file extension to the function that parses it.
READERS = {
    ".json" : _read_json,
    ".toml" : _read_toml,
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Format writers

def _write_json(path : Path, data : dict) -> None :
    """
    Write ``data`` to ``path`` using the ``json`` format.
    """

    with path.open("w", encoding = "utf-8") as file_handle :
        # ``sort_keys`` keeps the saved file stable across writes, which makes
        # diffing two configurations much easier.
        json.dump(data, file_handle, indent = 4, sort_keys = True)

# Map each supported file extension to the function that serialises it.
# Only ``json`` is writable for now: it is the format used to persist the
# configuration inside the tool's own config directory.
WRITERS = {
    ".json" : _write_json,
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public functions

def read_config_file(path : str | Path) -> dict :
    """
    Read a configuration file and return its content as a dictionary.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the configuration file. The format is inferred from the file
        extension (``.json`` or ``.toml``).

    Returns
    -------
    config : dict
        The parsed configuration dictionary.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not point to an existing file.
    ValueError
        If the file extension is not supported.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Input checks

    path = Path(path)

    if not path.is_file() :
        raise FileNotFoundError(f"Configuration file not found : {path}")

    extension = path.suffix.lower()

    if extension not in READERS :
        supported = ", ".join(sorted(READERS))
        raise ValueError(
            f"Unsupported configuration format '{extension}'. "
            f"Supported formats are : {supported}."
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Actual reading

    return READERS[extension](path)

def write_config_file(path : str | Path, data : dict) -> None :
    """
    Write a configuration dictionary to disk.

    Parameters
    ----------
    path : str or pathlib.Path
        Destination path. The format is inferred from the file extension.
    data : dict
        The configuration dictionary to serialise.

    Raises
    ------
    ValueError
        If the file extension is not supported for writing.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Input checks

    path        = Path(path)
    extension   = path.suffix.lower()

    if extension not in WRITERS :
        supported = ", ".join(sorted(WRITERS))
        raise ValueError(
            f"Unsupported configuration format '{extension}' for writing. "
            f"Supported formats are : {supported}."
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Actual writing

    # Make sure the parent directory exists before writing.
    path.parent.mkdir(parents = True, exist_ok = True)

    WRITERS[extension](path, data)
