"""
Per-round metric tracking for the ``autoresearch`` ``run`` command.

After each round the value of the optimised metric is appended to two files inside the experiment ``jlt_log_<name>`` folder :

- ``metrics.csv`` : a machine-readable table with one row per round (header ``round,<metric_name>``).
- ``metrics.txt`` : a human-readable log with one line per round.

Both files are appended to (never rewritten) so the full history across rounds is preserved.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import csv

# Specific imports
from pathlib import Path

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Name of the human-readable metric log.
METRICS_TXT_NAME = "metrics.txt"

# Name of the machine-readable metric table.
METRICS_CSV_NAME = "metrics.csv"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public functions

def append_metric(
        log_folder      : str | Path,
        round_number    : int,
        metric          : float,
        metric_name     : str = "metric",
    ) -> None :
    """
    Append the metric obtained in a round to the tracking files.

    Both ``metrics.csv`` and ``metrics.txt`` are updated.
    The csv header is written only the first time the file is created, so repeated calls keep a single, valid table.

    Parameters
    ----------
    log_folder : str or pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    round_number : int
        The round the metric belongs to.
    metric : float
        The metric value obtained in the round.
    metric_name : str, default ``"metric"``
        Name of the metric, used as the csv value-column header and in the human-readable log.
    """

    log_folder = Path(log_folder)

    _append_metric_csv(log_folder, round_number, metric, metric_name)
    _append_metric_txt(log_folder, round_number, metric, metric_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _append_metric_csv(
        log_folder      : Path,
        round_number    : int,
        metric          : float,
        metric_name     : str,
    ) -> None :
    """
    Append a single row to ``metrics.csv`` (writing the header if the file is new).

    Parameters
    ----------
    log_folder : pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    round_number : int
        The round the metric belongs to.
    metric : float
        The metric value obtained in the round.
    metric_name : str
        Name of the metric (used as the value-column header).
    """

    csv_path = log_folder / METRICS_CSV_NAME

    # The header must be written only once : check before opening in append mode.
    write_header = not csv_path.exists()

    with csv_path.open("a", encoding = "utf-8", newline = "") as file_handle :
        writer = csv.writer(file_handle)

        if write_header :
            writer.writerow(["round", metric_name])

        writer.writerow([round_number, metric])

def _append_metric_txt(
        log_folder      : Path,
        round_number    : int,
        metric          : float,
        metric_name     : str,
    ) -> None :
    """
    Append a single human-readable line to ``metrics.txt``.

    Parameters
    ----------
    log_folder : pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    round_number : int
        The round the metric belongs to.
    metric : float
        The metric value obtained in the round.
    metric_name : str
        Name of the metric (shown in the line).
    """

    txt_path = log_folder / METRICS_TXT_NAME

    with txt_path.open("a", encoding = "utf-8") as file_handle :
        file_handle.write(f"round {round_number} : {metric_name} = {metric}\n")
