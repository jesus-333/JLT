"""
Generic abstract template for every LLM backend used by JLT.

A *backend* is the object the rest of the tools talk to whenever they need an
LLM. The goal of this module is to provide a single, unified interface so that
each tool can stay completely agnostic about which provider (Ollama, Claude,
ChatGPT, GitHub Copilot, ...) is actually answering.

:class:`generic_backend` is an abstract base class. It implements everything
that does not depend on the specific provider (config loading/saving, reading
files, editing files) on top of two small provider specific primitives that
each subclass must implement:

- :meth:`~generic_backend.check_config` : validate a configuration dictionary.
- :meth:`~generic_backend._chat` : send a single prompt to the LLM and return
  its textual answer.

Every concrete backend (see e.g. :mod:`~jlt.shared_knowledge.backend.claude`)
must therefore be a child class of :class:`generic_backend`.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports section

from __future__ import annotations

# Full module imports
import abc

# Specific imports
from pathlib import Path

# Internal imports
from ..config_io import read_config_file, write_config_file

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module constants

# Plain text extensions a backend is allowed to write through :meth:`generic_backend.write_file`.
# Kept as a module level constant so the list of supported extensions can be extended in a single place.
SUPPORTED_WRITE_EXTENSIONS = ("txt", "md")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Abstract base class

class generic_backend(abc.ABC) :
    """
    Abstract template shared by every JLT LLM backend.

    Parameters
    ----------
    config_path : str or pathlib.Path
        Path to the file where this backend's configuration dictionary lives (or will be saved).
        If the file already exists it is read and validated through :meth:`update_config` during initialization.

    Attributes
    ----------
    config_path : pathlib.Path
        The path passed at construction time, where the configuration is
        persisted.
    config : dict or None
        The currently loaded configuration dictionary, or ``None`` if no
        configuration has been loaded yet.
    """

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Construction and configuration

    def __init__(self, config_path : str | Path) -> None :
        """
        Initialize the backend and load its configuration if available.
        """

        self.config_path    = Path(config_path)
        self.config         = None

        # If a configuration already exists at ``config_path`` load it now so the backend is immediately usable.
        # ``update_config`` takes care of validating it before storing it.
        # If the file does not exist yet, ``config`` is left as ``None`` : the backend is meant to be configured right after construction through :meth:`update_config` / :meth:`update_config_from_file` (this is exactly what :func:`~jlt.shared_knowledge.backend.registry.configure_backend` does when creating a brand new backend).
        # When a tool needs a ready to use backend it goes through :func:`~jlt.shared_knowledge.backend.registry.load_backend`, which guarantees the configuration file exists before constructing the backend.
        if self.config_path.is_file() :
            existing_config = read_config_file(self.config_path)
            self.update_config(existing_config)

    def update_config(self, config : dict) -> None :
        """
        Validate a configuration dictionary and persist it.

        The dictionary is first checked through :meth:`check_config` (which is backend specific).
        Only if the check passes is the configuration stored in memory and saved to :attr:`config_path`.

        Parameters
        ----------
        config : dict
            The configuration dictionary to apply.
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Validate the configuration (backend specific)

        self.check_config(config)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Store and persist the configuration

        self.config = config

        # The configuration is always persisted as ``json`` inside the tool's config directory, regardless of the format it was provided in.
        save_path = self.config_path.with_suffix(".json")
        write_config_file(save_path, config)

        # Keep ``config_path`` pointing at the file we actually wrote to.
        self.config_path = save_path

    def update_config_from_file(self, file_path : str | Path) -> None :
        """
        Read a configuration dictionary from a file and apply it.

        This is a thin wrapper around :meth:`update_config`: it simply reads the dictionary from ``file_path`` (supporting ``toml`` and ``json``) and forwards it.

        Parameters
        ----------
        file_path : str or pathlib.Path
            Path to a configuration file containing the dictionary.
        """

        config = read_config_file(file_path)
        self.update_config(config)

    @abc.abstractmethod
    def check_config(self, config : dict) -> None :
        """
        Validate a configuration dictionary (backend specific).

        Implementations must raise an exception (typically :class:`ValueError`) if ``config`` is not a valid configuration for the backend.
        The method is called by :meth:`update_config` before the configuration is saved.

        Parameters
        ----------
        config : dict
            The configuration dictionary to validate.
        """

        raise NotImplementedError

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Provider specific primitive

    @abc.abstractmethod
    def _chat(self, prompt : str, system : str | None = None) -> str :
        """
        Send a single prompt to the LLM and return its textual answer.

        This is the only provider specific call the high level methods (:meth:`modify_file`, :meth:`read_file`, ...) rely on. 
        Each concrete backend implements it using its own SDK / API.

        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        system : str, optional
            An optional system prompt that sets the behaviour of the model.

        Returns
        -------
        answer : str
            The model's textual answer.
        """

        raise NotImplementedError

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # File reading

    def read_file(self, file_to_read : str | Path, summarize : bool = False) -> str :
        """
        Read a text file and return its content as a string.

        Parameters
        ----------
        file_to_read : str or pathlib.Path
            Path to the text file to read.
        summarize : bool, default False
            If ``True`` the file content is passed to the LLM and a summary is
            returned instead of the raw content.

        Returns
        -------
        content : str
            The file content (or its summary if ``summarize`` is ``True``).
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Read the raw content

        path    = Path(file_to_read)
        content = path.read_text(encoding = "utf-8")

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Optionally summarize through the LLM

        if summarize :
            system_prompt = (
                "You are a helpful assistant. Summarize the text the user provides. "
                "Return only the summary, without any preamble."
            )
            content = self._chat(prompt = content, system = system_prompt)

        return content

    def read_files(self, list_of_files : list, summarize : bool = False) -> str :
        """
        Read several text files and return their content as a single string.

        Parameters
        ----------
        list_of_files : list
            A list of paths (``str`` or :class:`~pathlib.Path`) to read.
        summarize : bool, default False
            If ``True`` each file is summarized (through :meth:`read_file`)
            before being concatenated.

        Returns
        -------
        content : str
            The concatenation of every file's content. Each file is prefixed by
            a header reporting its path so the origin of each block stays clear.
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Read every file and store it in a single string

        blocks = []

        for single_file in list_of_files :
            # Reuse ``read_file`` so the summarize logic is not duplicated.
            single_content = self.read_file(single_file, summarize = summarize)

            # Add a small header so each block can be traced back to its file.
            header = f"# File : {single_file}"
            blocks.append(f"{header}\n{single_content}")

        return "\n\n".join(blocks)

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # File writing

    def write_file(
            self,
            text        : str,
            file_path   : str | Path,
            extension   : str = "txt",
        ) -> Path :
        """
        Create a text file containing ``text`` with the requested ``extension``.

        This is the counterpart of :meth:`read_file` : instead of reading an existing file it creates a brand new one from a string already in memory.
        It does not involve the LLM at all, it is a plain file write exposed on the backend so any tool (or the LLM driving it) has a single, uniform way to materialise text to disk.
        A typical use case is letting the LLM produce the content of, for example, a new experiment config for :mod:`~jlt.autoresearch` and then persist it.

        Parameters
        ----------
        text : str
            The content to write into the file.
        file_path : str or pathlib.Path
            Destination path of the file. Any suffix already present is replaced
            by ``extension`` so the resulting file always carries the requested
            extension. Missing parent directories are created automatically.
        extension : str, default ``"txt"``
            Extension of the file to create, given without the leading dot (a
            leading dot is tolerated and stripped). Only the extensions listed in
            :data:`SUPPORTED_WRITE_EXTENSIONS` (``txt`` and ``md``) are allowed.

        Returns
        -------
        written_path : pathlib.Path
            The path of the file that was actually written.

        Raises
        ------
        ValueError
            If ``extension`` is not one of :data:`SUPPORTED_WRITE_EXTENSIONS`.
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Input checks

        # Normalise the extension : drop a possible leading dot and lower the case so ``"MD"``, ``".md"`` and ``"md"`` are all treated the same.
        normalized_extension = extension.lstrip(".").lower()

        if normalized_extension not in SUPPORTED_WRITE_EXTENSIONS :
            supported = ", ".join(SUPPORTED_WRITE_EXTENSIONS)
            raise ValueError(
                f"Unsupported extension '{extension}' for writing. "
                f"Supported extensions are : {supported}."
            )

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Resolve the destination path

        # Force the chosen extension on the path so the caller can pass the
        # destination with or without a suffix and still get a coherent file.
        written_path = Path(file_path).with_suffix(f".{normalized_extension}")

        # Make sure the parent directory exists before writing.
        written_path.parent.mkdir(parents = True, exist_ok = True)

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Actual writing

        written_path.write_text(text, encoding = "utf-8")

        return written_path

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # File editing

    def modify_file(
            self,
            prompt          : str,
            file_to_edit    : str | Path,
            other_files     : str = None,
        ) -> str :
        """
        Modify a file following the instructions contained in ``prompt``.

        The current content of ``file_to_edit`` is sent to the LLM together with
        the instructions, and the model's answer is written back to the file.

        Parameters
        ----------
        prompt : str
            The instructions to follow. It can either be the instructions
            themselves or a path to a text file containing them. If ``prompt``
            points to an existing file its content is read (via
            :meth:`read_file`) and used as the instructions.
        file_to_edit : str or pathlib.Path
            Path to the file that has to be modified. The file is overwritten
            with the model's answer.
        other_files : str, optional
            Reserved for future use. The idea is to support prompts such as
            "I gave you N files with instructions, use them to modify this other
            file". Nothing is implemented for it yet.

        Returns
        -------
        new_content : str
            The new content written to ``file_to_edit``.
        """

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Resolve the prompt (direct instructions or path to a file)

        # If ``prompt`` is the path to an existing file, read the instructions
        # from it. Otherwise treat ``prompt`` as the instructions themselves.
        if isinstance(prompt, (str, Path)) and Path(prompt).is_file() :
            instructions = self.read_file(prompt)
        else :
            instructions = str(prompt)

        # ``other_files`` is intentionally not implemented yet (see docstring).
        # It is kept in the signature so the interface is already in place.

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Read the file to edit and build the prompt

        file_path       = Path(file_to_edit)
        current_content = file_path.read_text(encoding = "utf-8")

        system_prompt = (
            "You are a careful code/text editor. You receive the current "
            "content of a file and a set of instructions describing how to "
            "modify it. Return ONLY the full new content of the file, without "
            "any explanation, comment or markdown code fence."
        )

        user_prompt = (
            f"# Instructions\n{instructions}\n\n"
            f"# Current content of '{file_path}'\n{current_content}"
        )

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Query the LLM and write the answer back

        new_content = self._chat(prompt = user_prompt, system = system_prompt)

        file_path.write_text(new_content, encoding = "utf-8")

        return new_content
