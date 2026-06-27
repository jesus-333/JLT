"""
Shared code for the ``autoresearch`` example neural-network experiments.

This package is imported by each experiment's ``run.py`` (which adds this folder to ``sys.path`` first), so the two experiments share a single implementation of the model, the data pipeline and the training loop and differ only in how they wire it together.
"""
