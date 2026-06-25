"""CLI wiring for the ``autoresearch`` tool.

Invoked as::

    jlt autoresearch <subcommand, variable, flags>
"""

from __future__ import annotations

import argparse


def register(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Attach the ``autoresearch`` parser to the top-level ``jlt`` parser."""
    parser = subparsers.add_parser(
        "autoresearch",
        help="LLM-powered automated research tool.",
        description="LLM-powered automated research tool.",
    )
    # Tool subcommands / variables / flags will be added here as the tool grows.
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace) -> int:
    """Entry point for ``jlt autoresearch``."""
    print("jlt autoresearch: not implemented yet.")
    return 0
