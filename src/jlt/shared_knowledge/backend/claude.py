"""
Claude backend (Anthropic models).

This backend talks to Anthropic's models through the official ``anthropic``
Python SDK. It is a concrete implementation of
:class:`~jlt.shared_knowledge.backend.generic.generic_backend`.

The ``anthropic`` package is imported lazily (inside the methods that need it)
so that simply importing this module does not require the SDK to be installed.
This is what allows ``pip install jlt[claude]`` to pull only the Claude
dependencies.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Internal imports
from .generic import generic_backend

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# The string identifying this backend inside a configuration dictionary.
BACKEND_TYPE = "claude"

# Default model used when the configuration does not specify one.
DEFAULT_MODEL = "claude-opus-4-8"

# Default upper bound on the number of generated tokens. Streaming is always
# used (see ``_chat``) so this can be generous without risking HTTP timeouts.
DEFAULT_MAX_TOKENS = 16000

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Backend implementation

class claude_backend(generic_backend) :
    """
    Backend for all Anthropic (Claude) models.

    The configuration dictionary accepts the following keys :

    - ``backend_type`` : must be ``"claude"`` (mandatory).
    - ``api_key`` : the Anthropic API key. Optional: if missing, the SDK falls
      back to the ``ANTHROPIC_API_KEY`` environment variable.
    - ``model`` : the model id to use. Optional, defaults to
      :data:`DEFAULT_MODEL`.
    - ``max_tokens`` : maximum number of generated tokens. Optional, defaults to
      :data:`DEFAULT_MAX_TOKENS`.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Configuration check

    def check_config(self, config : dict) -> None :
        """
        Validate a configuration dictionary for the Claude backend.

        Parameters
        ----------
        config : dict
            The configuration dictionary to validate.

        Raises
        ------
        ValueError
            If ``config`` is not a dictionary or its ``backend_type`` does not
            match :data:`BACKEND_TYPE`.
        """

        if not isinstance(config, dict) :
            raise ValueError("The configuration must be a dictionary.")

        if config.get("backend_type") != BACKEND_TYPE :
            raise ValueError(
                f"Invalid 'backend_type' for the Claude backend. "
                f"Expected '{BACKEND_TYPE}', got '{config.get('backend_type')}'."
            )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # LLM primitive

    def _chat(self, prompt : str, system : str | None = None) -> str :
        """
        Send a single prompt to a Claude model and return its answer.

        Parameters
        ----------
        prompt : str
            The user prompt.
        system : str, optional
            An optional system prompt.

        Returns
        -------
        answer : str
            The model's textual answer.
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Lazy import of the SDK

        # Imported here so that the dependency is only required when the backend is actually used.
        import anthropic

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Build the client and the request parameters

        api_key     = self.config.get("api_key")
        model       = self.config.get("model", DEFAULT_MODEL)
        max_tokens  = self.config.get("max_tokens", DEFAULT_MAX_TOKENS)

        # ``api_key = None`` lets the SDK read ``ANTHROPIC_API_KEY`` from the environment.
        client = anthropic.Anthropic(api_key = api_key)

        # ``system`` must be omitted (not ``None``) when not provided.
        request_kwargs = {
            "model"      : model,
            "max_tokens" : max_tokens,
            "messages"   : [{"role" : "user", "content" : prompt}],
        }
        if system is not None :
            request_kwargs["system"] = system

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Query the model (streaming to avoid HTTP timeouts on long outputs)

        with client.messages.stream(**request_kwargs) as stream :
            message = stream.get_final_message()

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Extract and join the textual content blocks

        text_blocks = [block.text for block in message.content if block.type == "text"]

        return "".join(text_blocks)
