"""
Programmatic execution of an experiment ``run.py`` script.

An experiment folder contains a ``run.py`` script exposing a top-level ``run`` function that returns the numeric metric ``autoresearch`` has to optimise (this is checked statically at registration time by :mod:`~jlt.autoresearch.manage.validation`).

This module is in charge of actually *executing* that function : it imports ``run.py`` dynamically, runs ``run()`` from inside the experiment folder (so the experiment's own relative paths and imports keep working) and returns its numeric result.
The experiment code itself is never modified : only its configuration files are (see :mod:`~jlt.autoresearch.run.config_update`).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import importlib.util
import os
import sys

# Specific imports
from contextlib import contextmanager
from pathlib import Path

# Internal imports
# Reuse the script / function names already used by the static validation so the
# two stay in sync (a single source of truth).
from ..manage.validation import RUN_SCRIPT_NAME, RUN_FUNCTION_NAME

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Name under which the experiment ``run.py`` module is imported. It is arbitrary
# but kept distinctive to avoid clashing with a real module in ``sys.modules``.
_EXPERIMENT_MODULE_NAME = "jlt_autoresearch_experiment_run"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public function

def run_experiment_script(path_folder : str | Path) -> float :
    """
    Execute the ``run`` function of an experiment and return its numeric result.

    The ``run.py`` script found in ``path_folder`` is imported dynamically and its ``run`` function is called with the experiment folder as the working directory.
    The returned value is coerced to ``float`` : a non-numeric (or missing) result is treated as an error.

    Parameters
    ----------
    path_folder : str or pathlib.Path
        Path to the experiment folder (the one containing ``run.py``).

    Returns
    -------
    metric : float
        The numeric value returned by the experiment ``run`` function.

    Raises
    ------
    FileNotFoundError
        If ``run.py`` is missing.
    RuntimeError
        If ``run.py`` cannot be imported, does not expose a ``run`` function, the function raises, or its result cannot be converted to ``float``.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Locate the run script

    path_folder = Path(path_folder)
    run_script  = path_folder / RUN_SCRIPT_NAME

    if not run_script.is_file() :
        raise FileNotFoundError(f"The experiment run script was not found : {run_script}")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Import the script and grab the run function

    run_callable = _import_run_callable(run_script)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Execute it from inside the experiment folder

    # The experiment may use paths relative to its own folder (e.g. to read the
    # config files or write outputs), so run it with that folder as the cwd.
    with _working_directory(path_folder) :
        try :
            result = run_callable()
        except Exception as error :
            raise RuntimeError(
                f"The experiment 'run' function raised an exception : {error}"
            ) from error

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Coerce the result to a number

    # The static check at registration time only *warns* on a non-numeric (or
    # missing) annotation, so a runtime guard is still needed here.
    try :
        return float(result)
    except (TypeError, ValueError) as error :
        raise RuntimeError(
            f"The experiment 'run' function must return a numeric value, "
            f"but it returned : {result!r}."
        ) from error

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _import_run_callable(run_script : Path) :
    """
    Import an experiment ``run.py`` script and return its ``run`` function.

    Parameters
    ----------
    run_script : pathlib.Path
        Path to the ``run.py`` script to import.

    Returns
    -------
    run_callable : callable
        The top-level ``run`` function exposed by the script.

    Raises
    ------
    RuntimeError
        If the script cannot be imported or does not expose a callable ``run`` function.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Build a module spec and execute it

    spec = importlib.util.spec_from_file_location(_EXPERIMENT_MODULE_NAME, run_script)

    if spec is None or spec.loader is None :
        raise RuntimeError(f"Could not build an import spec for '{run_script}'.")

    module = importlib.util.module_from_spec(spec)

    # The experiment folder is prepended to ``sys.path`` for the duration of the
    # import so that ``run.py`` can import sibling modules / packages of its own.
    folder = str(run_script.parent)
    sys.path.insert(0, folder)
    try :
        spec.loader.exec_module(module)
    except Exception as error :
        raise RuntimeError(f"Could not import the experiment script '{run_script}' : {error}") from error
    finally :
        # Clean up both ``sys.path`` and ``sys.modules`` so repeated runs (and
        # other tools) are not affected by this temporary import.
        if folder in sys.path :
            sys.path.remove(folder)
        sys.modules.pop(_EXPERIMENT_MODULE_NAME, None)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Fetch the run function

    run_callable = getattr(module, RUN_FUNCTION_NAME, None)

    if not callable(run_callable) :
        raise RuntimeError(
            f"The experiment script '{run_script}' does not expose a callable "
            f"'{RUN_FUNCTION_NAME}' function."
        )

    return run_callable

@contextmanager
def _working_directory(path : str | Path) :
    """
    Temporarily change the current working directory.

    The previous working directory is always restored, even if the wrapped code raises.

    Parameters
    ----------
    path : str or pathlib.Path
        The directory to switch to for the duration of the ``with`` block.
    """

    previous_directory = Path.cwd()
    os.chdir(path)
    try :
        yield
    finally :
        os.chdir(previous_directory)
