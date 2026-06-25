"""
CLI wiring for the ``backend`` tool.

Invoked as::

    jlt backend <subcommand, variable, flags>

The ``backend`` tool manages the LLM backends shared across every JLT tool. It exposes the following subcommands :

- ``config`` : configure (create or update) a backend from a config file.
- ``list`` (alias ``ls``) : list the configured backends.
- ``activate`` : set which backend the tools should use.
- ``remove`` (alias ``rm``) : remove a configured backend.

The actual work is delegated to :mod:`~jlt.shared_knowledge.backend.registry`.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import argparse

# Internal imports
from . import registry

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Registration function

def register(subparsers : argparse._SubParsersAction) -> argparse.ArgumentParser :
    """
    Attach the ``backend`` parser to the top-level ``jlt`` parser.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction
        The subparsers action created by the top-level ``jlt`` parser (see
        :func:`~jlt.cli.build_parser`) to which this tool attaches itself.

    Returns
    -------
    parser : argparse.ArgumentParser
        The parser created for the ``backend`` tool.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the tool's parser

    parser = subparsers.add_parser(
        "backend",
        help        = "Manage the LLM backends shared across all tools.",
        description = "Manage the LLM backends shared across all tools.",
    )

    # If ``jlt backend`` is called with no subcommand, print the help.
    parser.set_defaults(func = lambda args : parser.print_help())

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the backend subcommands

    backend_subparsers = parser.add_subparsers(
        dest    = "backend_command",
        metavar = "<subcommand>",
        help    = "The backend operation to run.",
    )

    _register_config(backend_subparsers)
    _register_list(backend_subparsers)
    _register_activate(backend_subparsers)
    _register_remove(backend_subparsers)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Subcommand registration helpers

def _register_config(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``config`` subcommand.
    """

    parser = subparsers.add_parser(
        "config",
        help        = "Configure (create or update) a backend from a file.",
        description = "Configure (create or update) a backend from a file.",
    )

    parser.add_argument(
        "--backend_name",
        type     = str,
        required = True,
        help     = "Name under which the backend is saved (mandatory).",
    )

    parser.add_argument(
        "--path_file",
        type     = str,
        required = True,
        help     = "Path to a valid config file, toml or json (mandatory).",
    )

    parser.set_defaults(func = run_config)

def _register_list(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``list`` subcommand (alias ``ls``).
    """

    parser = subparsers.add_parser(
        "list",
        aliases     = ["ls"],
        help        = "Show all configured backends.",
        description = "Show all configured backends.",
    )

    parser.set_defaults(func = run_list)

def _register_activate(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``activate`` subcommand.
    """

    parser = subparsers.add_parser(
        "activate",
        help        = "Set which backend the tools should use.",
        description = "Set which backend the tools should use.",
    )

    parser.add_argument(
        "--backend_name",
        type     = str,
        required = True,
        help     = "Name of the backend to activate (mandatory). It must already be configured.",
    )

    parser.set_defaults(func = run_activate)

def _register_remove(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``remove`` subcommand (alias ``rm``).
    """

    parser = subparsers.add_parser(
        "remove",
        aliases     = ["rm"],
        help        = "Remove a configured backend.",
        description = "Remove a configured backend.",
    )

    parser.add_argument(
        "--backend_name",
        type     = str,
        required = True,
        help     = "Name of the backend to remove (mandatory). It must already be configured.",
    )

    parser.set_defaults(func = run_remove)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Subcommand entry points

def run_config(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt backend config``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``backend_name`` and ``path_file``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        registry.configure_backend(args.backend_name, args.path_file)
    except Exception as error :
        print(f"Error while configuring backend '{args.backend_name}' : {error}")
        return 1

    print(f"Backend '{args.backend_name}' configured successfully.")

    return 0

def run_list(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt backend list`` (and ``ls``).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (none used).

    Returns
    -------
    exit_code : int
        Always ``0``.
    """

    names   = registry.list_backends()
    active  = registry.get_active_backend_name()

    if not names :
        print("No backend configured yet.")
        return 0

    print("Configured backends :")
    for name in names :
        # Mark the active backend with an arrow for quick visual reference.
        marker = " <- active" if name == active else ""
        print(f"  - {name}{marker}")

    return 0

def run_activate(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt backend activate``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``backend_name``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        registry.set_active_backend(args.backend_name)
    except Exception as error :
        print(f"Error while activating backend '{args.backend_name}' : {error}")
        return 1

    print(f"Backend '{args.backend_name}' is now active.")

    return 0

def run_remove(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt backend remove`` (and ``rm``).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``backend_name``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        registry.remove_backend(args.backend_name)
    except Exception as error :
        print(f"Error while removing backend '{args.backend_name}' : {error}")
        return 1

    print(f"Backend '{args.backend_name}' removed successfully.")

    return 0
