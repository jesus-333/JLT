"""
Round-counter bookkeeping for the ``autoresearch`` ``run`` command.

Each registered experiment keeps a ``round.txt`` file inside its ``jlt_log_<name>`` folder.
The file holds a single integer : the number of the next round to run (numbering is 1-based, so the first round is round 1).
The ``run`` command reads it to know which round it is about to run and increments it once the round is complete.

The file is created (initialised to ``1``) at registration time by :func:`~jlt.autoresearch.manage.experiments._create_log_folder`, so the name of the file is defined there (:data:`~jlt.autoresearch.manage.experiments.ROUND_FILE_NAME`) and merely reused here to keep a single source of truth.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from pathlib import Path

# Internal imports
# ``ROUND_FILE_NAME`` is defined next to the other log-file-name constants so
# that registration and execution agree on the file name without duplicating it.
from ..manage.experiments import ROUND_FILE_NAME

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Round counter helpers

def get_round_file_path(log_folder : str | Path) -> Path :
    """
    Return the path of the ``round.txt`` file inside a log folder.

    Parameters
    ----------
    log_folder : str or pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.

    Returns
    -------
    path : pathlib.Path
        Path to the ``round.txt`` file (it may or may not exist yet).
    """

    return Path(log_folder) / ROUND_FILE_NAME

def read_round(log_folder : str | Path) -> int :
    """
    Read the current round number from a log folder.

    Parameters
    ----------
    log_folder : str or pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.

    Returns
    -------
    round_number : int
        The number of rounds executed so far.

    Raises
    ------
    FileNotFoundError
        If the ``round.txt`` file does not exist.
    ValueError
        If the file content is not a single integer.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Locate and read the file

    round_file = get_round_file_path(log_folder)

    if not round_file.is_file() :
        raise FileNotFoundError(
            f"Round counter file not found : {round_file}. "
            "The experiment may not have been registered correctly."
        )

    raw_content = round_file.read_text(encoding = "utf-8").strip()

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Parse the integer

    # A malformed counter is treated as a hard error rather than silently reset :
    # better safe than sorry (see the repo coding conventions).
    try :
        return int(raw_content)
    except ValueError as error :
        raise ValueError(
            f"The round counter file '{round_file}' does not contain a valid integer "
            f"(found : '{raw_content}')."
        ) from error

def write_round(log_folder : str | Path, round_number : int) -> None :
    """
    Overwrite the round counter of a log folder.

    Parameters
    ----------
    log_folder : str or pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    round_number : int
        The value to store in ``round.txt``.
    """

    round_file = get_round_file_path(log_folder)
    round_file.write_text(f"{round_number}\n", encoding = "utf-8")

def increment_round(log_folder : str | Path) -> int :
    """
    Increment the round counter of a log folder by one.

    Parameters
    ----------
    log_folder : str or pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.

    Returns
    -------
    new_round_number : int
        The value of the counter after the increment.
    """

    new_round_number = read_round(log_folder) + 1
    write_round(log_folder, new_round_number)

    return new_round_number
