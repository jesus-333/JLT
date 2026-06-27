"""
In-memory "conversation" helper for a single ``run`` round.

The spec requires that all the steps of one round happen "within the same LLM conversation, so that information is kept in memory".
The JLT backends are intentionally stateless (each :meth:`~jlt.shared_knowledge.backend.generic.generic_backend._chat` call is independent), so this module simulates a conversation on top of that : :class:`round_context` keeps an in-memory transcript of everything read and exchanged during the round and forwards it to the model on every new question.

This keeps the backend simple while still giving each step access to what the previous steps produced.
The class is also used to drive the small interactive exchange in which the LLM decides whether (and which) previous round reports it wants to read.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Round context

class round_context :
    """
    Accumulate the context of a single round and forward it to the backend.

    Every block added through :meth:`add` (the experiment description, the summary log, previous round reports, the exchanges so far) is kept in memory and prepended to the prompt of every subsequent :meth:`ask` call, simulating a single ongoing conversation on top of a stateless backend.

    Parameters
    ----------
    backend : jlt.shared_knowledge.backend.generic.generic_backend
        The backend used to answer the questions.

    Attributes
    ----------
    backend : jlt.shared_knowledge.backend.generic.generic_backend
        The backend used to answer the questions.
    blocks : list
        The list of ``(label, text)`` blocks making up the running transcript.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Construction

    def __init__(self, backend) -> None :
        """
        Initialise an empty round context bound to a backend.
        """

        self.backend = backend
        self.blocks  = []

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Building the transcript

    def add(self, label : str, text : str) -> None :
        """
        Append a labelled block of information to the running transcript.

        Parameters
        ----------
        label : str
            A short header describing the block (e.g. ``"Experiment description"``).
        text : str
            The content of the block.
        """

        self.blocks.append((label, text))

    def ask(self, prompt : str, system : str | None = None) -> str :
        """
        Ask the model a question, giving it the whole transcript as context.

        The current transcript is prepended to ``prompt`` and the exchange (question and answer) is itself appended to the transcript, so later questions can refer back to it.

        Parameters
        ----------
        prompt : str
            The question to ask.
        system : str, optional
            An optional system prompt.

        Returns
        -------
        answer : str
            The model's textual answer.
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Build the full prompt and query the backend

        full_prompt = (
            f"{self._render()}\n\n"
            "# Current request\n"
            f"{prompt}"
        )

        answer = self.backend.chat(full_prompt, system = system)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Record the exchange so it becomes part of the context

        self.add("Question", prompt)
        self.add("Answer", answer)

        return answer

    def render(self) -> str :
        """
        Return the current transcript as a single string.

        Returns
        -------
        transcript : str
            The whole transcript, each block prefixed by its label header.
        """

        return self._render()

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Helpers

    def _render(self) -> str :
        """
        Join every stored block into a single, headed transcript string.

        Returns
        -------
        transcript : str
            The concatenation of all blocks, each prefixed by ``# <label>``.
        """

        return "\n\n".join(f"# {label}\n{text}" for label, text in self.blocks)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Answer parsing helpers

def _parse_yes_no(answer : str) -> bool :
    """
    Interpret a free-form yes/no answer as a boolean.

    The answer is considered affirmative if, once stripped and lower-cased, it starts with ``y`` (so ``"yes"``, ``"Yes."``, ``"y"`` all map to ``True``).
    Anything else (including an empty answer) maps to ``False``, which is the safe default : when in doubt, do not read extra files.

    Parameters
    ----------
    answer : str
        The model's answer to a yes/no question.

    Returns
    -------
    affirmative : bool
        ``True`` if the answer is affirmative, ``False`` otherwise.
    """

    return answer.strip().lower().startswith("y")

def _parse_file_list(answer : str, available : list) -> list :
    """
    Interpret a free-form answer as a list of filenames.

    The answer is split on commas and newlines, each entry is stripped, and only the entries that actually appear in ``available`` are kept.
    Filtering against ``available`` discards any hallucinated or malformed filename, so the caller only ever receives real files.

    Parameters
    ----------
    answer : str
        The model's answer listing the files it wants to read.
    available : list
        The filenames that actually exist and may be read.

    Returns
    -------
    chosen : list
        The requested filenames that exist, in the order they appear in ``available`` (de-duplicated).
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Tokenise the answer

    # Normalise the separators (commas and newlines) to a single one, then split.
    raw_tokens = answer.replace("\n", ",").split(",")
    requested  = {token.strip() for token in raw_tokens if token.strip()}

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Keep only the real files (preserving the ``available`` order)

    return [name for name in available if name in requested]
