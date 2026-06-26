"""
Execution of a registered ``autoresearch`` experiment.

This module is in charge of *running* an experiment, i.e. driving the iterative loop in which an LLM modifies the experiment setup, ``autoresearch`` launches the experiment programmatically, and the LLM analyses the results before the next iteration.

.. note::
    For now this function is only a stub.
    The current implementation scope covers the CLI structure (subcommand parsing and dispatch wiring) only; the internal logic will be implemented in a later iteration.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Experiment execution function

def run_experiment(experiment_name : str) -> None :
    """
    Run a registered experiment.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment to run.
        It must already be registered (see :func:`~jlt.autoresearch.manage.add_experiment`).

    Raises
    ------
    NotImplementedError
        Always, until the internal logic is implemented.
    """

    raise NotImplementedError("'autoresearch run' is not implemented yet.")
