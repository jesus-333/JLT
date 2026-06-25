# Backend for LLM Management

Okay. Let's start working on the backend to manage the LLMs.

It must obviously be a subcommand of `jlt`, called with `jlt backend`.

At the Python code level, the following structure must be present:

```
src/
    jlt/
        cli.py                  ---> Top-level CLI entry point (the jlt command)
        tool_1/                 ---> Source code for tool 1
            cli.py              ---> CLI entry point for tool_1
            ...
        ...
        tool_n/                 ---> Source code for tool n
            cli.py              ---> CLI entry point for tool_n
            ...
        shared_knowledge/       ---> Source code shared by all tools
            backend/            ---> All the source code related to the backend
                generic.py      ---> Generic abstract class for backend implementation.
                backend_1.py    ---> Implementation of backend 1
                ...
                backend_n.py    ---> Implementation of backend n
                other_file...   ---> You could create other files if you think it's necessary
```

I placed the backend code inside `shared_knowledge` because it will most likely be reused by other tools in the future as well.

`generic.py` must be an abstract template class that provides a unified interface to the rest of the tools.
It must necessarily expose the following methods:

- `update_config()`: function to configure the backend (also called from `__init__()`). It must receive a dictionary with all the necessary configurations as input and save it at some path where the tool can retrieve it.
- `update_config_from_file()`: function that receives a path to a file containing the dictionary as input, reads it, and then uses `update_config` to update the config. Currently, `toml` and `json` must be supported. You can add other formats if you think it's useful.
- `check_config()`: backend-specific function that checks whether the config dictionary is valid. Called by `update_config` before saving the config.
- `__init__()`: which obviously receives the path to the dictionary as input.
- `modify_file(prompt: str, file_to_edit: str, other_files: str = None)`: modifies the file specified in `file_to_edit` following the `prompt`. The latter can be either direct instructions or the path to a text file containing the instructions. `other_files` is an extra parameter for now — nothing needs to be implemented for it. But my idea is to have it there in case I have a prompt like "I've passed you N files containing instructions. Use them to modify this other file."
- `read_file(file_to_read: str, summarize: bool = False)`: simply reads a text file and returns it as a string. Used for example by `modify_file` when the prompt is passed as a path. If `summarize` is set to true, it uses the LLM to produce a summary of what was read. I'm not yet sure in what other ways I might use it in the future, but I prefer to have it here.
- `read_files(list_of_files: list, summarize: bool = False)`: analogous to `read_file` but for a list of files. All read files are saved into a single string. If `summarize` is set to true, it summarizes each file before saving it.

Every specific backend must be a child class of `generic`.

Currently, I want the following backends to be implemented:

- `ollama` (both local and cloud)
- `claude` (for all Anthropic models)
- `chat_gpt` (for all OpenAI models)
- `github_copilot` (to interface with GitHub Copilot)

The CLI command must be invoked via `jlt backend`. From there, further subcommands must be available. For each of them I have also specified the flags:

- `config`: used to configure the backend
  - `--backend_name`: mandatory flag. Contains the name under which the backend is saved.
  - `--path_file`: path to a valid config file. This flag must be used mandatorily.
- `list`: to show all configured backends (can be abbreviated as `ls`)
- `activate`: internally sets which backend the tool should use
  - `--backend_name`: mandatory flag. Specifies the name of the backend to use. If it is not present in the list of configured backends, it raises an error.
- `remove`: removes the specified backend (can be abbreviated as `rm`)
  - `--backend_name`: mandatory flag. Specifies the name of the backend to remove. If it is not present in the list of configured backends, it raises an error.

Note that I can have multiple backends configured for the same provider. For example, if I have two paid Anthropic accounts, I can have 2 Claude backends configured (one per account, with different names obviously).

Also update `pyproject.toml` accordingly (new CLI functions, packages to install, etc.). Add the option to install only a specific backend if the user wants.
For example, if I only want to use `jlt` with Claude, I should be able to do `pip install jlt[claude]`.

If there is anything unclear before you start working, or if you need further instructions, feel free to ask.
