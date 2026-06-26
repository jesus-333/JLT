"""
Validation of an ``autoresearch`` experiment folder.

Before an experiment is registered (see :func:`~jlt.autoresearch.manage.experiments.add_experiment`) its folder must be checked to make sure it has the structure ``autoresearch`` expects :

- the folder exists,
- it contains a ``config`` sub-folder (where the experiment configuration files live),
- it contains a ``run.py`` script that exposes a ``run`` function returning a numeric value (the metric to optimise).

The folder is also expected (but not required) to contain an ``experiment_description`` file (either ``.txt`` or ``.md``) describing the experiment, its purpose and what it wants to achieve. This file is optional : when it is missing a warning is emitted, but the experiment is still accepted.

The ``run`` function is inspected **statically** through the :mod:`ast` module : the script is parsed but never imported nor executed, so checking an experiment is completely side-effect free (no risk of running arbitrary user code).

The numeric nature of the return value is checked through the function return annotation. Static analysis cannot always tell whether an annotation denotes a numeric type, therefore three outcomes are possible :

- the annotation is recognised as numeric : the check passes silently;
- the annotation is recognised as clearly non-numeric (e.g. ``str``, ``list``) : an error is raised;
- there is no annotation, or it cannot be classified : a warning is emitted and the experiment is accepted (the user is responsible for returning a numeric value).
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import ast
import warnings

# Specific imports
from pathlib import Path

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Name of the mandatory sub-folder holding the experiment configuration files.
CONFIG_SUBFOLDER_NAME = "config"

# Name of the mandatory script that starts the experiment.
RUN_SCRIPT_NAME = "run.py"

# Name of the mandatory function (inside ``run.py``) that runs the experiment.
RUN_FUNCTION_NAME = "run"

# Base name (without extension) of the optional file describing the experiment.
EXPERIMENT_DESCRIPTION_BASENAME = "experiment_description"

# Extensions accepted for the experiment description file.
EXPERIMENT_DESCRIPTION_EXTENSIONS = (".txt", ".md")

# Annotation identifiers that we accept as numeric. The comparison is done on a
# lower-cased identifier and matches by prefix, so numpy-like aliases such as
# ``float64`` or ``int32`` are recognised as well.
NUMERIC_TYPE_PREFIXES = ("int", "float", "complex", "number", "decimal")

# Annotation identifiers that are clearly NOT numeric. Returning one of these
# from the ``run`` function is considered an error.
NON_NUMERIC_TYPE_NAMES = {
    "str",
    "bytes",
    "bytearray",
    "bool",
    "list",
    "tuple",
    "dict",
    "set",
    "frozenset",
    "none",
    "nonetype",
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public function

def validate_experiment_folder(path_folder : str | Path) -> Path :
    """
    Check that ``path_folder`` is a valid ``autoresearch`` experiment folder.

    Parameters
    ----------
    path_folder : str or pathlib.Path
        Path to the experiment folder to validate.

    Returns
    -------
    path_folder : pathlib.Path
        The validated folder as a :class:`~pathlib.Path` (unchanged otherwise).

    Raises
    ------
    FileNotFoundError
        If the folder, the ``config`` sub-folder or the ``run.py`` script is missing.
    ValueError
        If ``run.py`` does not expose a ``run`` function, the function does not return a value, or its return annotation is recognised as non-numeric.

    Warns
    -----
    UserWarning
        If the optional ``experiment_description`` (``.txt``/``.md``) file is missing.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Check the folder and its mandatory content

    path_folder = Path(path_folder)

    # The folder itself must exist.
    if not path_folder.is_dir() :
        raise FileNotFoundError(f"Experiment folder not found : {path_folder}")

    # The ``config`` sub-folder must be present.
    config_subfolder = path_folder / CONFIG_SUBFOLDER_NAME
    if not config_subfolder.is_dir() :
        raise FileNotFoundError(
            f"The experiment folder must contain a '{CONFIG_SUBFOLDER_NAME}' sub-folder : {config_subfolder}"
        )

    # The ``run.py`` script must be present.
    run_script = path_folder / RUN_SCRIPT_NAME
    if not run_script.is_file() :
        raise FileNotFoundError(
            f"The experiment folder must contain a '{RUN_SCRIPT_NAME}' script : {run_script}"
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Check the run.py script

    _validate_run_script(run_script)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Check the optional experiment description file

    _check_experiment_description(path_folder)

    return path_folder

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Experiment description helper

def _check_experiment_description(path_folder : Path) -> None :
    """
    Check that the experiment folder contains a description file.

    The folder is expected (but not required) to contain an ``experiment_description`` file with a ``.txt`` or ``.md`` extension, describing the experiment, its purpose and what it wants to achieve. The file is optional : when none is found a warning is emitted, but the experiment is still accepted.

    Parameters
    ----------
    path_folder : pathlib.Path
        Path to the (already validated) experiment folder.
    """

    description_present = any(
        (path_folder / f"{EXPERIMENT_DESCRIPTION_BASENAME}{extension}").is_file()
        for extension in EXPERIMENT_DESCRIPTION_EXTENSIONS
    )

    if not description_present :
        accepted = " / ".join(
            f"{EXPERIMENT_DESCRIPTION_BASENAME}{extension}"
            for extension in EXPERIMENT_DESCRIPTION_EXTENSIONS
        )
        warnings.warn(
            f"No '{EXPERIMENT_DESCRIPTION_BASENAME}' file ({accepted}) was found in the "
            f"experiment folder. It is recommended to add one with a complete description "
            f"of the experiment, its purpose and what it wants to achieve.",
            UserWarning,
            stacklevel = 2,
        )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# run.py inspection helpers

def _validate_run_script(run_script : Path) -> None :
    """
    Check that the ``run.py`` script exposes a valid ``run`` function.

    Parameters
    ----------
    run_script : pathlib.Path
        Path to the ``run.py`` script.

    Raises
    ------
    ValueError
        If the script cannot be parsed, does not define a ``run`` function, the function returns nothing, or its return annotation is non-numeric.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Parse the script (without importing/executing it)

    source = run_script.read_text(encoding = "utf-8")

    try :
        tree = ast.parse(source)
    except SyntaxError as error :
        raise ValueError(f"The '{RUN_SCRIPT_NAME}' script contains a syntax error : {error}")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Locate the run function

    run_function_node = _find_run_function(tree)

    if run_function_node is None :
        raise ValueError(
            f"The '{RUN_SCRIPT_NAME}' script must define a '{RUN_FUNCTION_NAME}' function."
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Check that the function returns a value

    if not _function_returns_a_value(run_function_node) :
        raise ValueError(
            f"The '{RUN_FUNCTION_NAME}' function in '{RUN_SCRIPT_NAME}' must return a value (the metric to optimise)."
        )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Check (when possible) that the returned value is numeric

    _check_return_annotation(run_function_node)

def _find_run_function(tree : ast.Module) -> ast.FunctionDef | ast.AsyncFunctionDef | None :
    """
    Return the top-level ``run`` function node, or ``None`` if absent.

    Only functions defined at module level are considered : a ``run`` method nested inside a class or another function does not count.
    """

    for node in tree.body :
        is_function = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if is_function and node.name == RUN_FUNCTION_NAME :
            return node

    return None

def _function_returns_a_value(function_node : ast.FunctionDef | ast.AsyncFunctionDef) -> bool :
    """
    Return whether the given function contains a ``return <value>`` statement.

    A bare ``return`` (i.e. ``return None``) does not count. Return statements belonging to functions nested inside ``function_node`` are ignored, since they belong to a different scope.
    """

    for node in _walk_skipping_nested_scopes(function_node) :
        if isinstance(node, ast.Return) and node.value is not None :
            return True

    return False

def _walk_skipping_nested_scopes(function_node : ast.FunctionDef | ast.AsyncFunctionDef) :
    """
    Yield every descendant node of ``function_node`` without entering nested scopes.

    Nested functions, lambdas and classes introduce their own scope, so their bodies are skipped : only the statements that belong to ``function_node`` itself are visited.
    """

    # Start from the direct children of the function body.
    nodes_to_visit = list(function_node.body)

    while nodes_to_visit :
        node = nodes_to_visit.pop()
        yield node

        # Do not descend into nested scopes : their returns are not ours.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)) :
            continue

        nodes_to_visit.extend(ast.iter_child_nodes(node))

def _check_return_annotation(function_node : ast.FunctionDef | ast.AsyncFunctionDef) -> None :
    """
    Check the return annotation of the ``run`` function.

    Numeric annotation : pass silently.
    Recognised non-numeric annotation : raise an error.
    Missing or unclassifiable annotation : emit a warning and accept the experiment.

    Parameters
    ----------
    function_node : ast.FunctionDef or ast.AsyncFunctionDef
        The node of the ``run`` function.

    Raises
    ------
    ValueError
        If the annotation is recognised as a non-numeric type.
    """

    annotation = function_node.returns

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # No annotation : let it pass with a warning

    if annotation is None :
        warnings.warn(
            f"The '{RUN_FUNCTION_NAME}' function has no return type annotation : "
            f"it was not possible to verify that it returns a numeric value. "
            f"Make sure '{RUN_FUNCTION_NAME}' returns a numeric value.",
            UserWarning,
            stacklevel = 2,
        )
        return

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Classify the annotation

    annotation_name = _extract_annotation_name(annotation)

    # Annotation recognised as numeric : everything is fine.
    if annotation_name is not None and _name_is_numeric(annotation_name) :
        return

    # Annotation recognised as clearly non-numeric : this is an error.
    if annotation_name is not None and annotation_name.lower() in NON_NUMERIC_TYPE_NAMES :
        raise ValueError(
            f"The '{RUN_FUNCTION_NAME}' function is annotated to return '{annotation_name}', "
            f"which is not a numeric type. The metric to optimise must be numeric."
        )

    # Annotation present but not classifiable (e.g. a union or a generic) : warn.
    warnings.warn(
        f"Could not verify that the return type of the '{RUN_FUNCTION_NAME}' function is numeric. "
        f"Make sure '{RUN_FUNCTION_NAME}' returns a numeric value.",
        UserWarning,
        stacklevel = 2,
    )

def _extract_annotation_name(annotation : ast.expr) -> str | None :
    """
    Return a simple identifier for an annotation node, or ``None``.

    Handles the simple cases that cover the vast majority of return annotations :

    - a plain name (``float``)              -> ``"float"``
    - an attribute access (``np.float64``)  -> ``"float64"``
    - the ``None`` literal (``-> None``)    -> ``"None"``

    Anything more complex (unions, generics, ...) yields ``None``.
    """

    if isinstance(annotation, ast.Name) :
        return annotation.id

    if isinstance(annotation, ast.Attribute) :
        return annotation.attr

    if isinstance(annotation, ast.Constant) and annotation.value is None :
        return "None"

    return None

def _name_is_numeric(annotation_name : str) -> bool :
    """
    Return whether an annotation identifier denotes a numeric type.

    The match is done by prefix on the lower-cased identifier, so aliases such as ``float64`` or ``int32`` are recognised as numeric too.
    """

    annotation_name = annotation_name.lower()

    return any(annotation_name.startswith(prefix) for prefix in NUMERIC_TYPE_PREFIXES)
