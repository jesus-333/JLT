"""
Command line entry point for Jesus's LLM Tools (JLT).

JLT is a collection of LLM-powered tools. Every tool is invoked through the
single ``jlt`` command using the syntax::

    jlt <tool_name> <tool_subcommand, tool variable, tool flags>

Each tool lives in its own subpackage under ``jlt`` and exposes a
``register(subparsers)`` function in its ``cli`` module. That function attaches
the tool's own argument parser (with its subcommands, variables and flags) to
the shared top-level parser, keeping every tool self-contained.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import argparse

# Specific imports
from importlib import import_module

# Internal imports
from . import __version__

# Each entry maps a tool name to the module that exposes ``register(subparsers)``.
# Adding a new tool is a one-line change here.
TOOLS = (
    "jlt.autoresearch.cli",
    "jlt.club.cli",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Support function

def build_parser() -> argparse.ArgumentParser :
    """
    Build the top-level ``jlt`` parser and let every tool register itself.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build jlt parser

    parser = argparse.ArgumentParser(
        prog        = "jlt",
        description = "Jesus's LLM Tools (JLT): a collection of LLM-powered tools.",
    )

    parser.add_argument(
        "--version",
        action  = "version",
        version = f"%(prog)s {__version__}",
    )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build tool's parser

    subparsers = parser.add_subparsers(
        dest    = "tool",
        metavar = "<tool_name>",
        help    = "The JLT tool to run.",
    )
    subparsers.required = True

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Let every registered tool attach itself to the parser

    for module_path in TOOLS :
        module = import_module(module_path)
        module.register(subparsers)

    return parser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Main function

def main(argv : list[str] | None = None) -> int :
    """
    Parse ``argv`` and dispatch to the selected tool.

    Returns the tool's exit code (defaults to ``0``).
    """

    # Get input argument
    parser  = build_parser()
    args    = parser.parse_args(argv)

    # Note that ``func`` is set by each tool via ``set_defaults`` in its ``register``.
    return args.func(args) or 0

if __name__ == "__main__" :  # pragma: no cover
    raise SystemExit(main())
