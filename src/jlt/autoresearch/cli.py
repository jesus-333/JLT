"""
CLI wiring for the ``autoresearch`` tool.

Invoked as::

    jlt autoresearch <subcommand, variable, flags>
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
    Attach the ``autoresearch`` parser to the top-level ``jlt`` parser.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction
        The subparsers action created by the top-level ``jlt`` parser (see
        :func:`~jlt.cli.build_parser`) to which this tool attaches itself.

    Returns
    -------
    parser : argparse.ArgumentParser
        The parser created for the ``autoresearch`` tool.
    """

    # Create the tool's parser
    parser = subparsers.add_parser(
        "autoresearch",
        help        = "LLM-powered automated research tool.",
        description = "LLM-powered automated research tool.",
    )

    # Tool subcommands / variables / flags will be added here as the tool grows.
    parser.set_defaults(func = run)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Entry point

def run(args : argparse.Namespace) -> int :
    """
    Entry point for ``jlt autoresearch``.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed command line arguments for the ``autoresearch`` tool.

    Returns
    -------
    exit_code : int
        The exit code of the tool (``0`` on success).
    """

    print("jlt autoresearch: not implemented yet.")

    return 0
