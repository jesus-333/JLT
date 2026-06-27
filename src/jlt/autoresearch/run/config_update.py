"""
Safe update of the experiment configuration files during a ``run`` round.

Each round the LLM decides how to tweak the experiment hyperparameters.
The changes are applied to the files in the experiment ``config`` folder through the backend :meth:`~jlt.shared_knowledge.backend.generic.generic_backend.modify_file` method.

Because letting an LLM rewrite a structured file is error prone, the update is made robust :

1. before touching a file, a backup of its original content (raw text) and of its parsed keys is taken ;
2. the file is rewritten by the LLM ;
3. the rewritten file is parsed again and its keys are compared (recursively) against the backup keys.

If the keys do not match (or the file can no longer be parsed), the modification is considered failed : the original content is restored and the update is retried, up to :data:`MAX_CONFIG_RETRIES` times, before giving up with an error.

Only the *keys* are compared (not the values) : the whole point of a round is to change the values, while the set of hyperparameters must stay the same.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from pathlib import Path

# Internal imports
from ..manage.validation import CONFIG_SUBFOLDER_NAME
from jlt.shared_knowledge.config_io import read_config_file

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Configuration file formats ``autoresearch`` knows how to read back and check.
CONFIG_FILE_EXTENSIONS = (".json", ".toml")

# How many times a single config file update is retried before giving up.
MAX_CONFIG_RETRIES = 3

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public functions

def list_config_files(config_dir : str | Path) -> list :
    """
    Return the configuration files found in an experiment ``config`` folder.

    Parameters
    ----------
    config_dir : str or pathlib.Path
        The ``config`` sub-folder of the experiment.

    Returns
    -------
    config_files : list
        The sorted list of configuration files (``.json`` / ``.toml``) as :class:`~pathlib.Path` objects.

    Raises
    ------
    FileNotFoundError
        If ``config_dir`` does not exist.
    """

    config_dir = Path(config_dir)

    if not config_dir.is_dir() :
        raise FileNotFoundError(f"The '{CONFIG_SUBFOLDER_NAME}' folder was not found : {config_dir}")

    return sorted(
        path
        for path in config_dir.iterdir()
        if path.is_file() and path.suffix.lower() in CONFIG_FILE_EXTENSIONS
    )

def update_all_configs(backend, config_dir : str | Path, instructions : str) -> None :
    """
    Apply the round configuration update to every config file of an experiment.

    Parameters
    ----------
    backend : jlt.shared_knowledge.backend.generic.generic_backend
        The backend used to rewrite the files.
    config_dir : str or pathlib.Path
        The ``config`` sub-folder of the experiment.
    instructions : str
        The instructions describing how the configuration should change this round (typically the "Experiment Configuration Update" section the LLM just wrote).

    Raises
    ------
    FileNotFoundError
        If ``config_dir`` does not exist.
    RuntimeError
        If a config file could not be updated while keeping its set of keys intact.
    """

    for config_file in list_config_files(config_dir) :
        apply_config_update(backend, config_file, instructions)

def apply_config_update(backend, config_file : str | Path, instructions : str) -> None :
    """
    Rewrite a single config file following ``instructions``, keeping its keys intact.

    The file is rewritten by the backend and then validated : its parsed keys must match the keys it had before the update.
    On failure the original content is restored and the update is retried (up to :data:`MAX_CONFIG_RETRIES` times).

    Parameters
    ----------
    backend : jlt.shared_knowledge.backend.generic.generic_backend
        The backend used to rewrite the file.
    config_file : str or pathlib.Path
        Path to the configuration file to update.
    instructions : str
        The instructions describing how the configuration should change.

    Raises
    ------
    RuntimeError
        If, after :data:`MAX_CONFIG_RETRIES` attempts, the file still cannot be rewritten while preserving its set of keys.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Back up the original content and keys

    config_file = Path(config_file)

    original_text   = config_file.read_text(encoding = "utf-8")
    original_keys   = _collect_key_paths(read_config_file(config_file))

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Try to rewrite the file, validating the keys each time

    last_error = None

    for attempt in range(1, MAX_CONFIG_RETRIES + 1) :

        # Let the LLM rewrite the file in place.
        backend.modify_file(prompt = instructions, file_to_edit = config_file)

        # Re-parse and compare the keys. A parse failure (the LLM produced an
        # invalid file) is treated exactly like a key mismatch : a failed attempt.
        try :
            new_keys = _collect_key_paths(read_config_file(config_file))
        except Exception as error :
            last_error = f"the rewritten file could not be parsed ({error})"
            config_file.write_text(original_text, encoding = "utf-8")
            continue

        if new_keys == original_keys :
            # Success : the values may have changed but the set of keys is intact.
            return

        # Key mismatch : describe it, restore the original and retry.
        last_error = (
            f"the set of keys changed (missing : {sorted(original_keys - new_keys)}, "
            f"added : {sorted(new_keys - original_keys)})"
        )
        config_file.write_text(original_text, encoding = "utf-8")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # All attempts failed : restore the original and raise

    config_file.write_text(original_text, encoding = "utf-8")
    raise RuntimeError(
        f"Could not update the config file '{config_file}' while keeping its keys intact "
        f"after {MAX_CONFIG_RETRIES} attempts (last issue : {last_error})."
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _collect_key_paths(config : dict, prefix : tuple = ()) -> set :
    """
    Return the set of (nested) key-paths of a configuration dictionary.

    Each key is reported as the tuple of keys leading to it, so nested keys are distinguished from top-level ones and a renamed/dropped nested key is detected.

    Parameters
    ----------
    config : dict
        The configuration dictionary to inspect.
    prefix : tuple, default ``()``
        The chain of keys leading to ``config`` (used internally for the recursion).

    Returns
    -------
    key_paths : set
        The set of key-paths (each a tuple of keys).
    """

    key_paths = set()

    for key, value in config.items() :
        current_path = prefix + (key,)
        key_paths.add(current_path)

        # Recurse into nested dictionaries so the comparison covers every level.
        if isinstance(value, dict) :
            key_paths |= _collect_key_paths(value, current_path)

    return key_paths

def _config_keys_match(original : dict, modified : dict) -> bool :
    """
    Return whether two configuration dictionaries share the exact same key-paths.

    Parameters
    ----------
    original : dict
        The configuration before the update.
    modified : dict
        The configuration after the update.

    Returns
    -------
    match : bool
        ``True`` if both dictionaries have the same set of (nested) key-paths.
    """

    return _collect_key_paths(original) == _collect_key_paths(modified)
