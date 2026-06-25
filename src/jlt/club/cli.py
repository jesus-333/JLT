"""CLI wiring for the ``club`` tool.

Invoked as::

    jlt club <subcommand, variable, flags>
"""

from __future__ import annotations

import argparse


def register(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Attach the ``club`` parser to the top-level ``jlt`` parser."""
    parser = subparsers.add_parser(
        "club",
        help="LLM-powered club tool.",
        description="LLM-powered club tool.",
    )
    # Tool subcommands / variables / flags will be added here as the tool grows.
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace) -> int:
    """Entry point for ``jlt club``."""
    print("jlt club: not implemented yet.")
    return 0
