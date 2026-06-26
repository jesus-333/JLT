"""
Filesystem paths shared across all JLT tools.

Several tools need to know where JLT stores its data on disk (the *configuration directory*). This module centralises that resolution so every tool agrees on a single location, instead of each one re-deriving it.

The configuration directory is **not** tool specific : each tool namespaces its own data under ``<config_dir>/<tool_name>/`` (e.g. ``<config_dir>/backend/``, ``<config_dir>/autoresearch/``), with no exceptions.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import os

# Specific imports
from pathlib import Path

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Path helpers

def get_config_dir() -> Path :
    """
    Return the directory where JLT stores its configuration.

    The directory is resolved in the following order :

    1. The ``JLT_CONFIG_DIR`` environment variable, if set.
    2. ``$XDG_CONFIG_HOME/jlt``, if ``XDG_CONFIG_HOME`` is set.
    3. ``~/.config/jlt`` otherwise.

    Returns
    -------
    config_dir : pathlib.Path
        The (not necessarily existing) configuration directory.
    """

    if os.environ.get("JLT_CONFIG_DIR") :
        return Path(os.environ["JLT_CONFIG_DIR"])

    if os.environ.get("XDG_CONFIG_HOME") :
        return Path(os.environ["XDG_CONFIG_HOME"]) / "jlt"

    return Path.home() / ".config" / "jlt"
