"""
ChatGPT backend (OpenAI models).

This backend talks to OpenAI's models through the official ``openai`` Python SDK.
It is a concrete implementation of :class:`~jlt.shared_knowledge.backend.generic.generic_backend`.

The ``openai`` package is imported lazily so that simply importing this module does not require the SDK to be installed.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Internal imports
from .generic import generic_backend

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# The string identifying this backend inside a configuration dictionary.
BACKEND_TYPE = "chat_gpt"

# Default model used when the configuration does not specify one.
DEFAULT_MODEL = "gpt-4o"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Backend implementation

class chat_gpt_backend(generic_backend) :
    """
    Backend for all OpenAI (ChatGPT) models.

    The configuration dictionary accepts the following keys :

    - ``backend_type`` : must be ``"chat_gpt"`` (mandatory).
    - ``api_key`` : the OpenAI API key. Optional: if missing, the SDK falls back to the ``OPENAI_API_KEY`` environment variable.
    - ``model`` : the model id to use. Optional, defaults to :data:`DEFAULT_MODEL`.
    - ``base_url`` : a custom API base URL. Optional, useful for OpenAI compatible endpoints.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Configuration check

    def check_config(self, config : dict) -> None :
        """
        Validate a configuration dictionary for the ChatGPT backend.

        Parameters
        ----------
        config : dict
            The configuration dictionary to validate.

        Raises
        ------
        ValueError
            If ``config`` is not a dictionary or its ``backend_type`` does not match :data:`BACKEND_TYPE`.
        """

        if not isinstance(config, dict) :
            raise ValueError("The configuration must be a dictionary.")

        if config.get("backend_type") != BACKEND_TYPE :
            raise ValueError(
                f"Invalid 'backend_type' for the ChatGPT backend. "
                f"Expected '{BACKEND_TYPE}', got '{config.get('backend_type')}'."
            )

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # LLM primitive

    def _chat(self, prompt : str, system : str | None = None) -> str :
        """
        Send a single prompt to an OpenAI model and return its answer.

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

        from openai import OpenAI

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Build the client

        api_key     = self.config.get("api_key")
        model       = self.config.get("model", DEFAULT_MODEL)
        base_url    = self.config.get("base_url")

        # ``api_key = None`` lets the SDK read ``OPENAI_API_KEY`` from the
        # environment. ``base_url = None`` keeps the SDK default.
        client = OpenAI(api_key = api_key, base_url = base_url)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Build the message list and query the model

        messages = []
        if system is not None :
            messages.append({"role" : "system", "content" : system})
        messages.append({"role" : "user", "content" : prompt})

        response = client.chat.completions.create(model = model, messages = messages)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Extract the answer

        return response.choices[0].message.content
