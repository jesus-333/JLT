"""
GitHub Copilot backend.

GitHub Copilot exposes an OpenAI compatible chat endpoint, so this backend is
implemented on top of the ``openai`` Python SDK pointed at Copilot's API. It is
a concrete implementation of
:class:`~jlt.shared_knowledge.backend.generic.generic_backend`.

Authenticating against Copilot can require a token exchange that is outside the
scope of this backend: the ``api_key`` provided in the configuration is sent as
the bearer token as-is. If your setup needs a short lived Copilot token you must
obtain it beforehand and store it (or refresh it) in the configuration.

The ``openai`` package is imported lazily so that simply importing this module
does not require the SDK to be installed.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Internal imports
from .generic import generic_backend

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# The string identifying this backend inside a configuration dictionary.
BACKEND_TYPE = "github_copilot"

# Default OpenAI compatible base URL for GitHub Copilot.
DEFAULT_BASE_URL = "https://api.githubcopilot.com"

# Default model used when the configuration does not specify one.
DEFAULT_MODEL = "gpt-4o"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Backend implementation

class github_copilot_backend(generic_backend) :
    """
    Backend to interface with GitHub Copilot.

    The configuration dictionary accepts the following keys :

    - ``backend_type`` : must be ``"github_copilot"`` (mandatory).
    - ``api_key`` : the Copilot bearer token (mandatory).
    - ``model`` : the model id to use. Optional, defaults to
      :data:`DEFAULT_MODEL`.
    - ``base_url`` : the API base URL. Optional, defaults to
      :data:`DEFAULT_BASE_URL`.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Configuration check

    def check_config(self, config : dict) -> None :
        """
        Validate a configuration dictionary for the GitHub Copilot backend.

        Parameters
        ----------
        config : dict
            The configuration dictionary to validate.

        Raises
        ------
        ValueError
            If the dictionary has the wrong ``backend_type`` or is missing the
            mandatory ``api_key``.
        """

        if not isinstance(config, dict) :
            raise ValueError("The configuration must be a dictionary.")

        if config.get("backend_type") != BACKEND_TYPE :
            raise ValueError(
                f"Invalid 'backend_type' for the GitHub Copilot backend. "
                f"Expected '{BACKEND_TYPE}', got '{config.get('backend_type')}'."
            )

        if not config.get("api_key") :
            raise ValueError("The GitHub Copilot backend requires an 'api_key' entry.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # LLM primitive

    def _chat(self, prompt : str, system : str | None = None) -> str :
        """
        Send a single prompt to GitHub Copilot and return its answer.

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
        base_url    = self.config.get("base_url", DEFAULT_BASE_URL)

        # Copilot expects an integration id header in addition to the bearer
        # token; the OpenAI SDK forwards ``default_headers`` on every request.
        client = OpenAI(
            api_key         = api_key,
            base_url        = base_url,
            default_headers = {"Copilot-Integration-Id" : "vscode-chat"},
        )

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
