"""
GitHub Copilot backend.

This backend talks to GitHub Copilot through the official
``github-copilot-sdk`` package. It is a concrete implementation of
:class:`~jlt.shared_knowledge.backend.generic.generic_backend`.

Unlike a plain chat completion client, the Copilot SDK is an *agent runtime*:
it is async only, event based and drives a separate runtime binary (downloaded
once with ``python -m copilot download-runtime``, or fetched automatically on
the first call). This backend wraps that runtime back down to the small
synchronous :meth:`_chat` primitive the rest of JLT relies on, and it disables
all agent tools so the model only ever produces text (the file I/O lives in
:class:`~jlt.shared_knowledge.backend.generic.generic_backend`, not here).

Authentication is handled by the SDK : the ``api_key`` provided in the
configuration is an ordinary **GitHub token** (the same one ``gh auth token``
prints), not a pre-exchanged short lived Copilot bearer token. The SDK performs
the token exchange/refresh internally. If no token is configured the SDK falls
back to the logged-in GitHub user.

The ``copilot`` package is imported lazily so that simply importing this module
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

# Default model used when the configuration does not specify one.
DEFAULT_MODEL = "gpt-4o"

# Default timeout (in seconds) to wait for the assistant to finish a turn.
# Kept generous because ``modify_file`` can ask the model for a full file.
DEFAULT_TIMEOUT = 300

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Backend implementation

class github_copilot_backend(generic_backend) :
    """
    Backend to interface with GitHub Copilot.

    The configuration dictionary accepts the following keys :

    - ``backend_type`` : must be ``"github_copilot"`` (mandatory).
    - ``api_key`` : a GitHub token used to authenticate with Copilot. Optional :
      if missing, the SDK falls back to the logged-in GitHub user. The alias
      ``github_token`` is also accepted.
    - ``model`` : the model id to use. Optional, defaults to
      :data:`DEFAULT_MODEL`.
    - ``timeout`` : seconds to wait for a single answer. Optional, defaults to
      :data:`DEFAULT_TIMEOUT`.
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
            If ``config`` is not a dictionary or its ``backend_type`` does not
            match :data:`BACKEND_TYPE`.
        """

        if not isinstance(config, dict) :
            raise ValueError("The configuration must be a dictionary.")

        if config.get("backend_type") != BACKEND_TYPE :
            raise ValueError(
                f"Invalid 'backend_type' for the GitHub Copilot backend. "
                f"Expected '{BACKEND_TYPE}', got '{config.get('backend_type')}'."
            )

        # ``api_key`` is intentionally not required : the SDK can authenticate
        # through the logged-in GitHub user when no token is provided.

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

        # Imported here so that the dependency is only required when the backend is actually used.
        import asyncio

        from copilot import CopilotClient, PermissionHandler
        from copilot.session_events import AssistantMessageData

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Read the request parameters from the configuration

        github_token    = self.config.get("api_key") or self.config.get("github_token")
        model           = self.config.get("model", DEFAULT_MODEL)
        timeout         = self.config.get("timeout", DEFAULT_TIMEOUT)

        # The Copilot SDK exposes the system prompt as a "system message" config.
        # ``replace`` swaps the runtime's default system message for ours so the
        # behaviour matches the other (plain chat) backends.
        system_message = {"mode" : "replace", "content" : system} if system is not None else None

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Async helper driving the SDK

        async def _run() -> str :
            # Only forward ``github_token`` when set, otherwise let the SDK pick
            # up the logged-in GitHub user.
            client_kwargs = {}
            if github_token :
                client_kwargs["github_token"] = github_token

            session_kwargs = {
                "model"                 : model,
                "on_permission_request" : PermissionHandler.approve_all,
                # ``_chat`` must be pure text generation : give the agent no tools
                # so it never tries to touch the filesystem (JLT owns the file I/O).
                "available_tools"       : [],
            }
            if system_message is not None :
                session_kwargs["system_message"] = system_message

            async with CopilotClient(**client_kwargs) as client :
                async with await client.create_session(**session_kwargs) as session :
                    response = await session.send_and_wait(prompt, timeout = timeout)

            # ``send_and_wait`` returns the final assistant message event (or None).
            if response is not None and isinstance(response.data, AssistantMessageData) :
                return response.data.content or ""

            return ""

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Bridge the async SDK to the synchronous ``_chat`` contract

        # JLT's CLI is fully synchronous, so there is no running event loop here.
        # If ``_chat`` ever needed to be called from inside an event loop, this
        # would have to be replaced by running ``_run`` on a fresh loop instead.
        return asyncio.run(_run())
