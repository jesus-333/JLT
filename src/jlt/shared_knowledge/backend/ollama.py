"""
Ollama backend (local and cloud).

This backend talks to an Ollama server through the official ``ollama`` Python
package. It supports both a local server (the default ``http://localhost:11434``)
and the Ollama cloud service, selected through the ``mode`` configuration key.

The ``ollama`` package is imported lazily so that simply importing this module
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
BACKEND_TYPE = "ollama"

# Default host for a local Ollama server.
DEFAULT_LOCAL_HOST = "http://localhost:11434"

# Default host for the Ollama cloud service.
DEFAULT_CLOUD_HOST = "https://ollama.com"

# Supported running modes.
SUPPORTED_MODES = ("local", "cloud")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Backend implementation

class ollama_backend(generic_backend) :
    """
    Backend for Ollama, both local and cloud.

    The configuration dictionary accepts the following keys :

    - ``backend_type`` : must be ``"ollama"`` (mandatory).
    - ``model`` : the model id to use, e.g. ``"llama3.1"`` (mandatory).
    - ``mode`` : either ``"local"`` or ``"cloud"``. Optional, defaults to
      ``"local"``.
    - ``host`` : the server URL. Optional, defaults to
      :data:`DEFAULT_LOCAL_HOST` (local) or :data:`DEFAULT_CLOUD_HOST` (cloud).
    - ``api_key`` : the API key. Mandatory in ``cloud`` mode, ignored locally.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Configuration check

    def check_config(self, config : dict) -> None :
        """
        Validate a configuration dictionary for the Ollama backend.

        Parameters
        ----------
        config : dict
            The configuration dictionary to validate.

        Raises
        ------
        ValueError
            If the dictionary is malformed (wrong ``backend_type``, missing ``model``, invalid ``mode`` or missing cloud ``api_key``).
        """

        if not isinstance(config, dict) :
            raise ValueError("The configuration must be a dictionary.")

        if config.get("backend_type") != BACKEND_TYPE :
            raise ValueError(
                f"Invalid 'backend_type' for the Ollama backend. "
                f"Expected '{BACKEND_TYPE}', got '{config.get('backend_type')}'."
            )

        if not config.get("model") :
            raise ValueError("The Ollama backend requires a 'model' entry.")

        mode = config.get("mode", "local")
        if mode not in SUPPORTED_MODES :
            raise ValueError(
                f"Invalid 'mode' for the Ollama backend. "
                f"Expected one of {SUPPORTED_MODES}, got '{mode}'."
            )

        # In cloud mode an API key is mandatory.
        if mode == "cloud" and not config.get("api_key") :
            raise ValueError("The Ollama cloud mode requires an 'api_key' entry.")

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # LLM primitive

    def _chat(self, prompt : str, system : str | None = None) -> str :
        """
        Send a single prompt to the Ollama server and return its answer.

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

        from ollama import Client

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Resolve the connection parameters

        mode    = self.config.get("mode", "local")
        model   = self.config.get("model")

        # Pick a sensible default host depending on the mode.
        default_host    = DEFAULT_CLOUD_HOST if mode == "cloud" else DEFAULT_LOCAL_HOST
        host            = self.config.get("host", default_host)

        # In cloud mode the API key is passed as a bearer token.
        headers = {}
        if mode == "cloud" :
            headers["Authorization"] = f"Bearer {self.config.get('api_key')}"

        client = Client(host = host, headers = headers)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Build the message list and query the model

        messages = []
        if system is not None :
            messages.append({"role" : "system", "content" : system})
        messages.append({"role" : "user", "content" : prompt})

        response = client.chat(model = model, messages = messages)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Extract the answer

        return response["message"]["content"]
