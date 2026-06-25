"""
CLI wiring for the ``club`` tool.

Invoked as::

    jlt club <subcommand, variable, flags>
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import argparse

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Registration function

def register(subparsers : argparse._SubParsersAction) -> argparse.ArgumentParser :
    """
    Attach the ``club`` parser to the top-level ``jlt`` parser.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction
        The subparsers action created by the top-level ``jlt`` parser (see
        :func:`~jlt.cli.build_parser`) to which this tool attaches itself.

    Returns
    -------
    parser : argparse.ArgumentParser
        The parser created for the ``club`` tool.
    """

    # Create the tool's parser
    parser = subparsers.add_parser(
        "club",
        help        = "LLM-powered club tool.",
        description = "LLM-powered club tool.",
    )

    # Tool subcommands / variables / flags will be added here as the tool grows.
    parser.set_defaults(func = run)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Entry point

def run(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt club``.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed command line arguments for the ``club`` tool.

    Returns
    -------
    exit_code : int
        The exit code of the tool (``0`` on success).
    """

    print("jlt club: not implemented yet.")

    return 0
