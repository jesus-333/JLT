"""
Experiment management for the ``autoresearch`` tool.

This subpackage groups everything related to managing the *set* of experiments the user has registered (add, list, remove, ...).
It does **not** deal with actually running an experiment: that is the job of :mod:`~jlt.autoresearch.run`.

The public functions are re-exported here so the rest of the package can simply do ``from jlt.autoresearch import manage`` and call ``manage.add_experiment(...)``.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Internal imports
from .experiments import add_experiment, list_experiments, remove_experiment

__all__ = [
    "add_experiment",
    "list_experiments",
    "remove_experiment",
]
