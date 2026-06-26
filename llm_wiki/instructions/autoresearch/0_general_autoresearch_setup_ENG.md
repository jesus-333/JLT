# `autoresearch` — CLI Tool Specification

As the name suggests, this tool is meant to be a CLI version of the idea Karpathy developed with
[autoresearch](https://github.com/karpathy/autoresearch/tree/master).

## High-level workflow

0. The user configures the LLM backend they want to use (Ollama, Claude, ChatGPT, etc.).
1. The user creates the experiment files and saves them in a folder.
2. `autoresearch` inspects the files and any extra instructions provided by the user.
3. The experiment running loop:
   1. An LLM instance is created and modifies the experiment setup. **The experiment code itself must never be modified.**
   2. `autoresearch` launches the experiment programmatically — **not** through the LLM.
   3. Once the experiment finishes, the LLM analyses the results and draws conclusions for the next iteration.
   4. Steps 3.1–3.3 repeat until a convergence criterion is satisfied.
4. A final report is produced.

> Many complex details have been intentionally omitted here (e.g. convergence criterion, allowed experiment structure).
> These will be discussed when each specific component (or sub-component) is implemented.

## Python package structure

```
src/
    jlt/
        cli.py              # Top-level CLI entry point (the `jlt` command)
        autoresearch/       # Source code for the autoresearch tool
            cli.py          # CLI entry point for autoresearch
            manage/         # Code related to experiment management (add, remove, configure, list, etc.)
            run/            # Code related to running experiments — to be implemented later
            ...             # Any other files/folders deemed useful
        shared_knowledge/   # Source code shared across all tools
            ...
```

## CLI interface

The command is invoked as `jlt autoresearch` (with the alias `jlt ar`).

### Subcommands

#### `add`

Registers a new experiment. Note: this command does **not** copy the experiment files — it only
saves the path internally.

| Flag | Required | Description |
|---|---|---|
| `--path_folder` | ✅ Yes | Path to a valid experiment config folder. |
| `--experiment_name` | No | Name under which to register the experiment. Defaults to the name of the folder. |

#### `list` (alias: `ls`)

Displays all experiments currently in the registry.

#### `remove` (alias: `rm`)

Removes the specified experiment from the registry.

| Flag | Required | Description |
|---|---|---|
| `--experiment_name` | ✅ Yes | Name of the experiment to remove. |

#### `run`

Executes the specified experiment.

| Flag | Required | Description |
|---|---|---|
| `--experiment_name` | ✅ Yes | Name of the experiment to run. |

## Dispatch mapping

| CLI subcommand | Python function | Location |
|---|---|---|
| `add` | `add_experiment(...)` | `autoresearch/manage/` |
| `list` / `ls` | `list_experiments(...)` | `autoresearch/manage/` |
| `remove` / `rm` | `remove_experiment(...)` | `autoresearch/manage/` |
| `run` | `run_experiment(...)` | `autoresearch/run/` |

## Implementation scope (current)

For now, only the **CLI structure** (subcommand parsing and dispatch wiring) should be implemented.
The internal logic of each subcommand will be addressed separately in future iterations.

> **Note:** Additional subcommands beyond those listed here may be added in the future.
