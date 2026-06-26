"""
CLI wiring for the ``autoresearch`` tool.

Invoked as (with the alias ``ar``)::

    jlt autoresearch <subcommand, variable, flags>
    jlt ar           <subcommand, variable, flags>

``autoresearch`` is a CLI take on Karpathy's `autoresearch` idea : the user registers an experiment config folder and the tool iteratively lets an LLM tweak the experiment setup, runs the experiment and analyses the results.
It exposes the following subcommands :

- ``add`` : register a new experiment (only the path is saved, the files are not copied).
- ``list`` (alias ``ls``) : list the registered experiments.
- ``remove`` (alias ``rm``) : remove a registered experiment.
- ``run`` : run a registered experiment.

The actual work is delegated to :mod:`~jlt.autoresearch.manage` (registry operations) and :mod:`~jlt.autoresearch.run` (experiment execution).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import argparse

# Internal imports
from . import manage, run

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Registration function

def register(subparsers : argparse._SubParsersAction) -> argparse.ArgumentParser :
    """
    Attach the ``autoresearch`` parser to the top-level ``jlt`` parser.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction
        The subparsers action created by the top-level ``jlt`` parser (see :func:`~jlt.cli.build_parser`) to which this tool attaches itself.

    Returns
    -------
    parser : argparse.ArgumentParser
        The parser created for the ``autoresearch`` tool.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the tool's parser

    parser = subparsers.add_parser(
        "autoresearch",
        aliases     = ["ar"],
        help        = "LLM-powered automated research tool.",
        description = "LLM-powered automated research tool.",
    )

    # If ``jlt autoresearch`` is called with no subcommand, print the help.
    parser.set_defaults(func = lambda args : parser.print_help())

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Create the autoresearch subcommands

    autoresearch_subparsers = parser.add_subparsers(
        dest    = "autoresearch_command",
        metavar = "<subcommand>",
        help    = "The autoresearch operation to run.",
    )

    _register_add(autoresearch_subparsers)
    _register_list(autoresearch_subparsers)
    _register_remove(autoresearch_subparsers)
    _register_run(autoresearch_subparsers)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Subcommand registration helpers

def _register_add(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``add`` subcommand.
    """

    parser = subparsers.add_parser(
        "add",
        help        = "Register a new experiment (the files are not copied, only the path is saved).",
        description = "Register a new experiment (the files are not copied, only the path is saved).",
    )

    parser.add_argument(
        "--path_folder",
        type     = str,
        required = True,
        help     = "Path to a valid experiment config folder (mandatory).",
    )

    parser.add_argument(
        "--experiment_name",
        type     = str,
        required = False,
        default  = None,
        help     = "Name under which to register the experiment (optional). Defaults to the name of the folder.",
    )

    parser.set_defaults(func = run_add)

def _register_list(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``list`` subcommand (alias ``ls``).
    """

    parser = subparsers.add_parser(
        "list",
        aliases     = ["ls"],
        help        = "Show all registered experiments.",
        description = "Show all registered experiments.",
    )

    parser.set_defaults(func = run_list)

def _register_remove(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``remove`` subcommand (alias ``rm``).
    """

    parser = subparsers.add_parser(
        "remove",
        aliases     = ["rm"],
        help        = "Remove a registered experiment.",
        description = "Remove a registered experiment.",
    )

    parser.add_argument(
        "--experiment_name",
        type     = str,
        required = True,
        help     = "Name of the experiment to remove (mandatory). It must already be registered.",
    )

    parser.set_defaults(func = run_remove)

def _register_run(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``run`` subcommand.
    """

    parser = subparsers.add_parser(
        "run",
        help        = "Run a registered experiment.",
        description = "Run a registered experiment.",
    )

    parser.add_argument(
        "--experiment_name",
        type     = str,
        required = True,
        help     = "Name of the experiment to run (mandatory). It must already be registered.",
    )

    parser.set_defaults(func = run_run)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Subcommand entry points

def run_add(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch add``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``path_folder`` and ``experiment_name``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        manage.add_experiment(args.path_folder, args.experiment_name)
    except Exception as error :
        print(f"Error while adding experiment : {error}")
        return 1

    return 0

def run_list(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch list`` (and ``ls``).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (none used).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        experiments = manage.list_experiments()
    except Exception as error :
        print(f"Error while listing experiments : {error}")
        return 1

    if not experiments :
        print("No experiment registered yet.")
        return 0

    print("Registered experiments :")
    for experiment_name in experiments :
        print(f"  - {experiment_name}")

    return 0

def run_remove(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch remove`` (and ``rm``).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``experiment_name``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        manage.remove_experiment(args.experiment_name)
    except Exception as error :
        print(f"Error while removing experiment '{args.experiment_name}' : {error}")
        return 1

    print(f"Experiment '{args.experiment_name}' removed successfully.")

    return 0

def run_run(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch run``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``experiment_name``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        run.run_experiment(args.experiment_name)
    except Exception as error :
        print(f"Error while running experiment '{args.experiment_name}' : {error}")
        return 1

    return 0
