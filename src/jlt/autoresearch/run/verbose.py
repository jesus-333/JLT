"""
Helpers to echo the LLM reasoning/output during a verbose ``run`` round.

When ``jlt autoresearch run`` is called with ``--verbose`` / ``-v`` the raw text produced by the LLM at every step of the round is printed to the terminal.
This is purely a debugging aid : it lets the user follow what the model "reasons" and what it writes into the config / log files, without having to open the generated files afterwards.

All the printing goes through :func:`print_llm_output` so the format of the verbose blocks stays consistent across the different steps of a round.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Width of the separator lines that frame a verbose block.
SEPARATOR_WIDTH = 70

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public functions

def print_llm_output(label : str, text : str) -> None :
    """
    Print a labelled block of LLM output to the terminal.

    The block is framed by two separator lines so the verbose output is easy to spot among the regular ``run`` progress messages.

    Parameters
    ----------
    label : str
        A short header describing what the block contains (e.g. ``"LLM answer"``).
    text : str
        The raw text produced by the LLM.
    """

    separator = "-" * SEPARATOR_WIDTH

    print(separator)
    print(f"[verbose] {label}")
    print(separator)
    print(text)
    print(separator)
