"""
Shared code for the ``autoresearch`` example scikit-learn experiment.

This package is imported by the experiment's ``run.py`` (which adds this folder to ``sys.path`` first), so the experiment shares a single implementation of the data pipeline, the classifier factory and the train / evaluate loop, and the experiment folder itself stays limited to ``run.py``, its ``config`` folder and the description.
"""
