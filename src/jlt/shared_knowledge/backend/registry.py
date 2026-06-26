"""
Registry of configured backends.

While :mod:`~jlt.shared_knowledge.backend.generic` (and its subclasses) describe *how* a single backend behaves, this module manages the *set* of backends the user has configured.
It manages where their configurations live on disk, which provider each one uses, and which one is currently active.

Several backends can be configured for the same provider. For example two Claude accounts can be saved under two different names.
Each configured backend is stored as a ``json`` file named after the chosen backend name.

Layout of the configuration directory ::

    <config_dir>/
        active.json             ---> stores the name of the active backend
        backends/
            <backend_name>.json ---> one file per configured backend
            ...

The configuration directory defaults to ``~/.config/jlt`` and can be overridden
with the ``JLT_CONFIG_DIR`` environment variable (or ``XDG_CONFIG_HOME``).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from pathlib import Path

# Internal imports
from ..config_io import read_config_file, write_config_file
from ..paths import get_config_dir
from .generic import generic_backend
from .ollama import ollama_backend
from .claude import claude_backend
from .chat_gpt import chat_gpt_backend
from .github_copilot import github_copilot_backend

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Map each ``backend_type`` to the class that implements it. Adding a new
# provider is a one-line change here (plus the new backend module).
BACKEND_CLASSES = {
    "ollama"         : ollama_backend,
    "claude"         : claude_backend,
    "chat_gpt"       : chat_gpt_backend,
    "github_copilot" : github_copilot_backend,
}

# Name of the file storing the active backend pointer.
ACTIVE_FILE_NAME = "active.json"

# Name of the sub-directory holding one config file per configured backend.
BACKENDS_DIR_NAME = "backends"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Path helpers

def get_backends_dir() -> Path :
    """
    Return the directory holding one config file per configured backend.
    """

    return get_config_dir() / BACKENDS_DIR_NAME

def get_backend_config_path(backend_name : str) -> Path :
    """
    Return the path of the config file for a given backend name.

    Parameters
    ----------
    backend_name : str
        The name under which the backend is (or will be) saved.

    Returns
    -------
    path : pathlib.Path
        Path to the ``<backend_name>.json`` file.
    """

    return get_backends_dir() / f"{backend_name}.json"

def get_active_file_path() -> Path :
    """
    Return the path of the file storing the active backend pointer.
    """

    return get_config_dir() / ACTIVE_FILE_NAME

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Backend class resolution

def get_backend_class(backend_type : str) -> type :
    """
    Return the backend class associated with a ``backend_type``.

    Parameters
    ----------
    backend_type : str
        The provider identifier (e.g. ``"claude"``).

    Returns
    -------
    backend_class : type
        The class implementing the requested backend.

    Raises
    ------
    ValueError
        If ``backend_type`` is unknown.
    """

    if backend_type not in BACKEND_CLASSES :
        supported = ", ".join(sorted(BACKEND_CLASSES))
        raise ValueError(
            f"Unknown backend type '{backend_type}'. "
            f"Supported types are : {supported}."
        )

    return BACKEND_CLASSES[backend_type]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Listing / activation / removal

def list_backends() -> list :
    """
    Return the sorted list of configured backend names.

    Returns
    -------
    names : list
        The names of every configured backend (empty if none).
    """

    backends_dir = get_backends_dir()

    if not backends_dir.is_dir() :
        return []

    # Each configured backend is a ``.json`` file; the stem is its name.
    return sorted(path.stem for path in backends_dir.glob("*.json"))

def get_active_backend_name() -> str | None :
    """
    Return the name of the active backend, or ``None`` if none is set.
    """

    active_file = get_active_file_path()

    if not active_file.is_file() :
        return None

    return read_config_file(active_file).get("active")

def set_active_backend(backend_name : str) -> None :
    """
    Set the active backend.

    Parameters
    ----------
    backend_name : str
        The name of the backend to activate. It must already be configured.

    Raises
    ------
    ValueError
        If ``backend_name`` is not in the list of configured backends.
    """

    if backend_name not in list_backends() :
        raise ValueError(
            f"Backend '{backend_name}' is not configured. "
            f"Configure it first with 'jlt backend config'."
        )

    write_config_file(get_active_file_path(), {"active" : backend_name})

def remove_backend(backend_name : str) -> None :
    """
    Remove a configured backend.

    Parameters
    ----------
    backend_name : str
        The name of the backend to remove. It must already be configured.

    Raises
    ------
    ValueError
        If ``backend_name`` is not in the list of configured backends.
    """

    if backend_name not in list_backends() :
        raise ValueError(f"Backend '{backend_name}' is not configured.")

    # Delete the configuration file.
    get_backend_config_path(backend_name).unlink()

    # If the removed backend was the active one, clear the active pointer.
    if get_active_backend_name() == backend_name :
        active_file = get_active_file_path()
        if active_file.is_file() :
            active_file.unlink()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Configuration / instantiation

def configure_backend(backend_name : str, path_file : str | Path) -> generic_backend :
    """
    Configure (create or update) a named backend from a configuration file.

    The provider is inferred from the ``backend_type`` entry of the file. The
    matching backend class is instantiated and its configuration saved under
    ``backend_name`` inside the JLT configuration directory.

    Parameters
    ----------
    backend_name : str
        The name under which the backend is saved.
    path_file : str or pathlib.Path
        Path to a valid configuration file (``toml`` or ``json``).

    Returns
    -------
    backend : generic_backend
        The configured backend instance.

    Raises
    ------
    ValueError
        If the file does not specify a valid ``backend_type``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Determine the provider from the configuration file

    config          = read_config_file(path_file)
    backend_type    = config.get("backend_type")
    backend_class   = get_backend_class(backend_type)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Instantiate the backend at its destination path and load the config

    destination = get_backend_config_path(backend_name)

    # The destination file does not exist yet (or holds an old config); the
    # backend is created pointing at it, then ``update_config_from_file`` reads
    # the user provided file, validates it and saves it at the destination.
    backend = backend_class(destination)
    backend.update_config_from_file(path_file)

    return backend

def load_backend(backend_name : str | None = None) -> generic_backend :
    """
    Instantiate a configured backend, ready to be used by a tool.

    Parameters
    ----------
    backend_name : str, optional
        The name of the backend to load. If ``None`` the active backend is loaded instead.

    Returns
    -------
    backend : generic_backend
        The instantiated backend.

    Raises
    ------
    ValueError
        If no backend name is given and none is active, or if the requested backend is not configured.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Resolve which backend to load

    if backend_name is None :
        backend_name = get_active_backend_name()
        if backend_name is None :
            raise ValueError(
                "No active backend set. Activate one with'jlt backend activate --backend_name <name>'."
            )

    if backend_name not in list_backends() :
        raise ValueError(f"Backend '{backend_name}' is not configured.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Read the saved config to find the provider, then instantiate

    config_path     = get_backend_config_path(backend_name)
    backend_type    = read_config_file(config_path).get("backend_type")
    backend_class   = get_backend_class(backend_type)

    # The constructor reads and validates the existing config file.
    return backend_class(config_path)
