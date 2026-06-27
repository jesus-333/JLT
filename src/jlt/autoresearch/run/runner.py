"""
Execution of a registered ``autoresearch`` experiment (one optimisation round).

This module drives a single *round* of the optimisation loop. From inside the experiment folder it :

1. reads the experiment description and the summary of the previous rounds ;
2. (optionally) lets the LLM read previous per-round reports for more context ;
3. lets the LLM decide how to tweak the experiment configuration and records that decision in the round log ;
4. applies the configuration changes (safely, keeping the set of keys intact) ;
5. runs the experiment programmatically and records the obtained metric ;
6. lets the LLM analyse the result and updates the summary log ;
7. increments the round counter and, as the very last step, backs everything up into the tool's internal mirror.

All the steps of one round share a single in-memory transcript (:class:`~jlt.autoresearch.run.conversation.round_context`) so that information read early in the round is still available to the later steps, even though the underlying backend is stateless.
The experiment *code* is never modified : only its configuration files are.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Specific imports
from pathlib import Path

# Internal imports
from . import config_update, metrics_io, round_io
from .conversation import round_context, _parse_yes_no, _parse_file_list
from .experiment_runner import run_experiment_script
from .round_template import load_round_template
from .sync import sync_experiment
from ..manage import registry
from ..manage.experiments import SUMMARY_LOG_FILE_NAME
from ..manage.validation import (
    CONFIG_SUBFOLDER_NAME,
    EXPERIMENT_DESCRIPTION_BASENAME,
    EXPERIMENT_DESCRIPTION_EXTENSIONS,
)
from jlt.shared_knowledge.backend import load_backend

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# The three section headers of the round log template. They are matched verbatim
# when the round file is (re)built, so they must stay in sync with
# :data:`~jlt.autoresearch.run.round_template.ROUND_TEMPLATE`.
SECTION_SUMMARY      = "Summary Previous Rounds"
SECTION_CONFIG       = "Experiment Configuration Update"
SECTION_RESULT       = "Result and analysis"

# Placeholder used in the round file for a section that has not been filled yet.
SECTION_PLACEHOLDER = "_(not filled yet)_"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Experiment execution function

def run_experiment(experiment_name : str) -> None :
    """
    Run a single optimisation round of a registered experiment.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment to run.
        It must already be registered (see :func:`~jlt.autoresearch.manage.add_experiment`).

    Raises
    ------
    ValueError
        If the experiment is not registered.
    FileNotFoundError
        If a mandatory file (description, summary log, run script, ...) is missing.
    RuntimeError
        If the configuration update or the experiment execution fails.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Resolve the experiment and prepare the round context

    info        = registry.read_experiment_info(experiment_name)
    path_folder = Path(info["path_folder"])
    log_folder  = Path(info["log_folder"])
    config_dir  = path_folder / CONFIG_SUBFOLDER_NAME
    metric_name = info["metric_name"]
    direction   = info["optimization_direction"]

    backend = load_backend()
    context = round_context(backend)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Read the mandatory context (description + summary log)

    description = _load_description(path_folder)
    context.add("Experiment description", description)

    current_round   = round_io.read_round(log_folder)
    round_path      = log_folder / f"round_{current_round}.md"

    summary_log = (log_folder / SUMMARY_LOG_FILE_NAME).read_text(encoding = "utf-8")
    context.add("Summary log of previous rounds", summary_log)

    print(f"Running round {current_round} of experiment '{experiment_name}' "
          f"(optimising '{metric_name}', {direction}).")

    # Materialise the round file from the internal template right away so it
    # exists (in its canonical, empty form) even if a later step fails. The
    # sections are then filled in place as the round progresses.
    round_path.write_text(load_round_template(), encoding = "utf-8")
    sections = {
        SECTION_SUMMARY : SECTION_PLACEHOLDER,
        SECTION_CONFIG  : SECTION_PLACEHOLDER,
        SECTION_RESULT  : SECTION_PLACEHOLDER,
    }

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Optionally read previous round reports for more context

    _maybe_read_previous_rounds(context, backend, log_folder, current_round)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Let the LLM write the "summary" and "config update" sections

    sections[SECTION_SUMMARY] = context.ask(
        "Based on the experiment description, the summary log and any previous round "
        "reports above, write a VERY BRIEF summary of what the previous rounds did and "
        "found. Return ONLY the summary text, without any markdown header."
    ).strip()
    _write_round_file(round_path, sections)

    config_instructions = context.ask(
        f"Now decide how to change the experiment configuration for THIS round in order to "
        f"improve the metric '{metric_name}' (optimisation direction : {direction}). "
        "Describe what you want to change and why. Be concrete : state which hyperparameters "
        "to set and to which values. IMPORTANT : you may only change the VALUES of the "
        "existing hyperparameters, never add, remove or rename keys. Return ONLY the "
        "description text, without any markdown header."
    ).strip()
    sections[SECTION_CONFIG] = config_instructions
    _write_round_file(round_path, sections)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Apply the configuration changes (safely)

    config_update.update_all_configs(
        backend      = backend,
        config_dir   = config_dir,
        instructions = _build_config_instructions(config_instructions),
    )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Run the experiment and record the metric

    metric = run_experiment_script(path_folder)
    print(f"Round {current_round} finished : {metric_name} = {metric}.")

    metrics_io.append_metric(log_folder, current_round, metric, metric_name)
    context.add("Result of this round", f"{metric_name} = {metric}")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Let the LLM analyse the result and update the logs

    sections[SECTION_RESULT] = context.ask(
        f"The experiment has been run with the updated configuration and the obtained value "
        f"of '{metric_name}' is {metric}. Considering the optimisation direction ({direction}) "
        "and the previous rounds, write the result and your analysis for this round. Return "
        "ONLY the analysis text, without any markdown header."
    ).strip()
    _write_round_file(round_path, sections)

    _update_summary_log(backend, context, log_folder, current_round, metric_name, metric, direction)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Bump the round counter and back everything up (last step)

    round_io.increment_round(log_folder)
    sync_experiment(experiment_name)

    print(f"Round {current_round} of experiment '{experiment_name}' completed and synced.")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Helper functions

def _load_description(path_folder : Path) -> str :
    """
    Read the mandatory ``experiment_description`` file of an experiment.

    Both supported extensions (``.txt`` / ``.md``) are probed.

    Parameters
    ----------
    path_folder : pathlib.Path
        The experiment folder.

    Returns
    -------
    description : str
        The content of the description file.

    Raises
    ------
    FileNotFoundError
        If no ``experiment_description`` file is found.
    """

    for extension in EXPERIMENT_DESCRIPTION_EXTENSIONS :
        candidate = path_folder / f"{EXPERIMENT_DESCRIPTION_BASENAME}{extension}"
        if candidate.is_file() :
            return candidate.read_text(encoding = "utf-8")

    raise FileNotFoundError(
        f"No '{EXPERIMENT_DESCRIPTION_BASENAME}' file "
        f"({' / '.join(EXPERIMENT_DESCRIPTION_EXTENSIONS)}) found in {path_folder}."
    )

def _maybe_read_previous_rounds(context : round_context, backend, log_folder : Path, current_round : int) -> None :
    """
    Run the interactive "read previous rounds ?" exchange and load the chosen files.

    The LLM is first asked whether it wants to read previous round reports (yes/no).
    If yes, it is given the list of available report files and asked which ones to read ; the chosen files are loaded and added to the round context.

    Parameters
    ----------
    context : jlt.autoresearch.run.conversation.round_context
        The running round context (updated in place).
    backend : jlt.shared_knowledge.backend.generic.generic_backend
        The backend used to read the chosen files.
    log_folder : pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    current_round : int
        The round about to be run (its own report, if any, is excluded from the choice).
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Nothing to read if there is no previous report

    available_files = _list_previous_round_files(log_folder, current_round)

    if not available_files :
        return

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Ask whether the LLM wants to read any of them

    wants_to_read = _parse_yes_no(context.ask(
        "Some reports from previous rounds are available. Do you want to read any of them "
        "to gain more context before deciding the configuration for this round ? "
        "Answer strictly with a single word : yes or no."
    ))

    if not wants_to_read :
        return

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Ask which ones, then load them

    available_names = [path.name for path in available_files]

    answer = context.ask(
        "Here are the available previous round files : "
        f"{', '.join(available_names)}. "
        "Reply strictly with a comma-separated list of the exact filenames you want to read "
        "(or an empty answer for none)."
    )

    chosen_names = _parse_file_list(answer, available_names)

    if not chosen_names :
        return

    chosen_paths = [log_folder / name for name in chosen_names]
    context.add("Selected previous round reports", backend.read_files(chosen_paths))

def _list_previous_round_files(log_folder : Path, current_round : int) -> list :
    """
    Return the previous ``round_<i>.md`` report files of an experiment.

    Parameters
    ----------
    log_folder : pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    current_round : int
        The round about to be run : its own ``round_<current_round>.md`` file is excluded.

    Returns
    -------
    files : list
        The sorted list of previous round report files (as :class:`~pathlib.Path`).
    """

    current_file = f"round_{current_round}.md"

    return sorted(
        path
        for path in log_folder.glob("round_*.md")
        if path.name != current_file
    )

def _build_config_instructions(config_update_text : str) -> str :
    """
    Wrap the round's configuration decision into per-file edit instructions.

    Each config file is edited independently through :meth:`~jlt.shared_knowledge.backend.generic.generic_backend.modify_file`, so the instructions must remind the model to only touch values and keep the file structure intact.

    Parameters
    ----------
    config_update_text : str
        The free-form description of the changes to apply (written by the LLM earlier in the round).

    Returns
    -------
    instructions : str
        The instructions passed to ``modify_file`` for every config file.
    """

    return (
        "Apply the following configuration changes to this file.\n\n"
        f"{config_update_text}\n\n"
        "Rules :\n"
        "- Only change the VALUES of the existing keys ; never add, remove or rename keys.\n"
        "- Keep the original file format and structure intact.\n"
        "- If a described change does not apply to this particular file, leave that file unchanged."
    )

def _update_summary_log(
        backend,
        context         : round_context,
        log_folder      : Path,
        round_number    : int,
        metric_name     : str,
        metric          : float,
        direction       : str,
    ) -> None :
    """
    Update the experiment ``summary_log.md`` after a round.

    The current summary log is rewritten by the LLM to incorporate the result of the round just completed, while keeping the cumulative history of the previous rounds.

    Parameters
    ----------
    backend : jlt.shared_knowledge.backend.generic.generic_backend
        The backend used to rewrite the file.
    context : jlt.autoresearch.run.conversation.round_context
        The running round context (its transcript is forwarded to the model).
    log_folder : pathlib.Path
        The ``jlt_log_<name>`` folder of the experiment.
    round_number : int
        The round just completed.
    metric_name : str
        Name of the optimised metric.
    metric : float
        The metric value obtained in the round.
    direction : str
        The optimisation direction (``"ascending"`` / ``"descending"``).
    """

    summary_path = log_folder / SUMMARY_LOG_FILE_NAME

    instructions = (
        "# Context of the round just completed\n"
        f"{context.render()}\n\n"
        "# Your task\n"
        f"Update this summary log to incorporate round {round_number} : the configuration that "
        f"was tried and the obtained value of '{metric_name}' ({metric}), keeping in mind the "
        f"optimisation direction ({direction}). Keep a concise, cumulative summary of ALL rounds "
        "so far (do not drop the information about the previous rounds). Return the full new "
        "content of the summary log."
    )

    backend.modify_file(prompt = instructions, file_to_edit = summary_path)

def _write_round_file(round_path : Path, sections : dict) -> None :
    """
    (Re)write a ``round_<i>.md`` file from the template, filling its sections.

    The file is rebuilt from the template every time so that the three section headers always stay present and in order, regardless of how many of them are already filled.

    Parameters
    ----------
    round_path : pathlib.Path
        Destination path of the round file.
    sections : dict
        Mapping from section title (one of :data:`SECTION_SUMMARY`, :data:`SECTION_CONFIG`, :data:`SECTION_RESULT`) to the text to put under that header.
    """

    # The body is rebuilt from ``sections`` (rather than patched in place) so the
    # three headers always stay present and in order, even on a partial round.
    content = (
        f"# {SECTION_SUMMARY}\n\n{sections[SECTION_SUMMARY]}\n\n"
        f"# {SECTION_CONFIG}\n\n{sections[SECTION_CONFIG]}\n\n"
        f"# {SECTION_RESULT}\n\n{sections[SECTION_RESULT]}\n"
    )

    round_path.write_text(content, encoding = "utf-8")
