"""
Template of the per-round log file (``round_<i>.md``) produced by the ``run`` command.

Every round the ``run`` command writes a fresh ``round_<i>.md`` file inside the experiment ``jlt_log_<name>`` folder and then fills its three sections (through the LLM) as the round progresses :

- ``Summary Previous Rounds`` : a brief recap of what previous rounds did and found.
- ``Experiment Configuration Update`` : what the configuration changes for this round are, and why.
- ``Result and analysis`` : the result obtained with the chosen configuration and its analysis.

The template is kept here as a plain module-level string (rather than a data file) so that it ships with the package automatically and needs no special packaging handling.
A human-readable copy also lives in the wiki at ``llm_wiki/instructions/autoresearch/template_round_i.md`` for documentation purposes ; this module is the authoritative runtime source.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Template

# The three section headers are matched verbatim by the runner when it fills a
# single section : keep them in sync with :mod:`~jlt.autoresearch.run.runner`.
ROUND_TEMPLATE = (
    "# Summary Previous Rounds\n"
    "\n"
    "IN THIS SECTION YOU SHOULD PUT A VERY BRIEF SUMMARY OF THE RESULTS OF THE PREVIOUS ROUND\n"
    "\n"
    "# Experiment Configuration Update\n"
    "\n"
    "IN THIS SECTION YOU SHOULD WRITE WHAT YOU WANT TO DO IN THIS ROUND AND WHY.\n"
    "\n"
    "# Result and analysis\n"
    "\n"
    "AFTER RUNNING THE EXPERIMENT IN THIS SECTION YOU SHOULD WRITE THE RESULTS AND THE ANALYSIS FOR THE CURRENT CONFIGURATION\n"
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Public functions

def load_round_template() -> str :
    """
    Return the content of the per-round log template.

    Returns
    -------
    template : str
        The markdown template used to initialise a new ``round_<i>.md`` file.
    """

    return ROUND_TEMPLATE
