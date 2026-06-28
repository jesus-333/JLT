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
- ``sync`` : copy an experiment results between its log folder and the tool's internal backup.

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
    _register_sync(autoresearch_subparsers)

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
        required = False,
        default  = None,
        help     = "Path to a valid experiment folder. Mandatory, unless --experiment_info_path is used.",
    )

    parser.add_argument(
        "--experiment_name",
        type     = str,
        required = False,
        default  = None,
        help     = "Name under which to register the experiment (optional). Defaults to the name of the folder.",
    )

    parser.add_argument(
        "--metric_name",
        type     = str,
        required = False,
        default  = None,
        help     = "Name of the metric to optimise. Mandatory, unless --experiment_info_path is used.",
    )

    # The optimisation direction : exactly one of the two flags is expected (the
    # mutually exclusive group forbids passing both at the same time).
    direction_group = parser.add_mutually_exclusive_group()

    direction_group.add_argument(
        "--ascending",
        action = "store_true",
        help   = "Maximise the metric. Cannot be combined with --descending.",
    )

    direction_group.add_argument(
        "--descending",
        action = "store_true",
        help   = "Minimise the metric. Cannot be combined with --ascending.",
    )

    parser.add_argument(
        "--experiment_info_path",
        type     = str,
        required = False,
        default  = None,
        help     = (
            "Path to a json/toml file holding every field above "
            "(path_folder, experiment_name, metric_name, ascending/descending). "
            "When used, no other flag can be passed."
        ),
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

    parser.add_argument(
        "--verbose", "-v",
        action = "store_true",
        help   = "Print the reasoning/output produced by the LLM during the round (useful for debugging). Default : False.",
    )

    parser.set_defaults(func = run_run)

def _register_sync(subparsers : argparse._SubParsersAction) -> None :
    """
    Register the ``sync`` subcommand.
    """

    parser = subparsers.add_parser(
        "sync",
        help        = "Copy an experiment results between its log folder and the tool's internal backup.",
        description = "Copy an experiment results between its log folder and the tool's internal backup.",
    )

    parser.add_argument(
        "--experiment_name",
        type     = str,
        required = False,
        default  = None,
        help     = "Name of the experiment to synchronise (optional). Defaults to the name of the current folder.",
    )

    parser.add_argument(
        "--reverse",
        action = "store_true",
        help   = "Reverse the direction : copy the internal backup into the experiment log folder instead.",
    )

    parser.set_defaults(func = run_sync)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Subcommand entry points

def run_add(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch add``.

    The experiment can be described either directly through the individual flags (``--path_folder``, ``--metric_name``, ``--ascending``/``--descending``, ``--experiment_name``) or through a single ``--experiment_info_path`` file. The two ways are mutually exclusive.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``path_folder``, ``experiment_name``, ``metric_name``, ``ascending``, ``descending`` and ``experiment_info_path``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        if args.experiment_info_path is not None :
            # Every field comes from the file : no other flag is allowed.
            _ensure_no_conflicting_flags(args)
            experiment_name = manage.add_experiment_from_info_file(args.experiment_info_path)
        else :
            # Fields come from the individual flags : check the mandatory ones.
            _ensure_required_add_flags(args)
            experiment_name = manage.add_experiment(
                path_folder     = args.path_folder,
                metric_name     = args.metric_name,
                ascending       = args.ascending,
                experiment_name = args.experiment_name,
            )
    except Exception as error :
        print(f"Error while adding experiment : {error}")
        return 1

    print(f"Experiment '{experiment_name}' added successfully.")

    return 0

def _ensure_no_conflicting_flags(args : argparse.Namespace) -> None :
    """
    Check that ``--experiment_info_path`` is not combined with any other flag.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed ``add`` arguments.

    Raises
    ------
    ValueError
        If any other ``add`` flag is set alongside ``--experiment_info_path``.
    """

    conflicting = (
        args.path_folder is not None
        or args.experiment_name is not None
        or args.metric_name is not None
        or args.ascending
        or args.descending
    )

    if conflicting :
        raise ValueError(
            "--experiment_info_path cannot be combined with any other flag "
            "(path_folder, experiment_name, metric_name, ascending, descending)."
        )

def _ensure_required_add_flags(args : argparse.Namespace) -> None :
    """
    Check that the flags mandatory for a direct ``add`` are all present.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed ``add`` arguments.

    Raises
    ------
    ValueError
        If ``--path_folder``, ``--metric_name`` or the optimisation direction is missing. The mutually exclusive group already guarantees that ``--ascending`` and ``--descending`` are not passed together.
    """

    if args.path_folder is None :
        raise ValueError("--path_folder is required (or use --experiment_info_path).")

    if args.metric_name is None :
        raise ValueError("--metric_name is required (or use --experiment_info_path).")

    if not args.ascending and not args.descending :
        raise ValueError("One of --ascending / --descending is required (or use --experiment_info_path).")

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
        Parsed arguments (uses ``experiment_name`` and ``verbose``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        run.run_experiment(args.experiment_name, verbose = args.verbose)
    except Exception as error :
        print(f"Error while running experiment '{args.experiment_name}' : {error}")
        return 1

    return 0

def run_sync(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch sync``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments (uses ``experiment_name`` and ``reverse``).

    Returns
    -------
    exit_code : int
        ``0`` on success, ``1`` on error.
    """

    try :
        run.sync_experiment(experiment_name = args.experiment_name, reverse = args.reverse)
    except Exception as error :
        print(f"Error while syncing experiment '{args.experiment_name}' : {error}")
        return 1

    print("Sync completed successfully.")

    return 0
