"""
Experiment execution for the ``autoresearch`` tool.

This subpackage groups everything related to *running* a registered experiment (the iterative experiment loop described in the tool specification).
Managing the *set* of registered experiments is instead the job of :mod:`~jlt.autoresearch.manage`.

The public functions are re-exported here so the rest of the package can simply do ``from jlt.autoresearch import run`` and call ``run.run_experiment(...)``.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Internal imports
from .runner import run_experiment

__all__ = [
    "run_experiment",
]
