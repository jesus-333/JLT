# Autoresearch Subsystem Summary

The **autoresearch** tool is a CLI take on the *autoresearch* idea : the user
registers an experiment, and `autoresearch` will (in a later iteration)
iteratively let an LLM tweak the experiment setup, run it, and analyse the
results in order to optimise a numeric metric.

This document covers the **experiment configuration** part that is implemented
today : the `add`, `list` and `remove` commands. The `run` command (the
optimisation loop itself) is still a stub.

## Index

- [Key ideas](#key-ideas)
- [What is an experiment](#what-is-an-experiment)
- [CLI reference](#cli-reference)
- [CLI examples](#cli-examples)
- [Where things are stored](#where-things-are-stored)
- [Python implementation](#python-implementation)

## Key ideas

- An **experiment** is an iterative hyperparameter optimisation process. Because
  it is iterative, the same experiment can be run several times (each run is a
  **round**).
- Registering an experiment does **not** copy its files : only the path to the
  experiment folder (plus a little metadata) is saved internally.
- Each experiment is saved under a **name** you choose (defaults to the folder
  name).

## What is an experiment

An experiment is a folder containing the scripts that do the actual work
(numerical simulations, neural-network training, ...). The folder **must**
contain :

- a `config` sub-folder, holding the experiment configuration files (for now
  only `toml` and `json` are accepted);
- a `run.py` script that starts the experiment. It must expose a `run` function
  that returns the numeric value `autoresearch` has to optimise. When the `run`
  command is implemented, this is exactly the function that will be executed.

At registration time `run.py` is inspected **statically** (it is parsed but
never imported nor executed) to check that :

- a top-level `run` function exists;
- it actually returns a value (checked through the `ast` module);
- its return type annotation is numeric. If the annotation is recognised as
  numeric the check passes; if it is recognised as clearly non-numeric (e.g.
  `str`) an error is raised; if there is no annotation (or it cannot be
  classified) a warning is emitted and the experiment is accepted.

## CLI reference

```
jlt autoresearch add    --path_folder <path> --metric_name <name> (--ascending | --descending) [--experiment_name <name>]
jlt autoresearch add    --experiment_info_path <path>      # every field read from a json/toml file
jlt autoresearch list                                      # list (alias: ls)
jlt autoresearch remove --experiment_name <name>           # remove from the registry (alias: rm)
```

`autoresearch` can also be abbreviated as `ar`.

- `--ascending` maximises the metric, `--descending` minimises it. Exactly one
  is required and they cannot be combined.
- `--experiment_info_path` points to a `json`/`toml` file holding all the fields
  above (`path_folder`, `metric_name`, `ascending`/`descending`,
  `experiment_name`). When used, no other flag can be passed.
- `remove` only deletes the registry entry : the original experiment folder and
  the `jlt_log_<experiment_name>` folder next to it are left untouched.

## CLI examples

```bash
# Register an experiment, maximising "accuracy"
jlt ar add --path_folder ./my_experiment --metric_name accuracy --ascending

# Same, but reading everything from a file
cat info.toml
# path_folder     = "./my_experiment"
# experiment_name = "my_experiment"
# metric_name     = "loss"
# descending      = true
jlt ar add --experiment_info_path info.toml

# List and remove
jlt ar ls
jlt ar rm --experiment_name my_experiment
```

## Where things are stored

When an experiment is registered, its information is saved in **two** places.
The duplication is intentional : it keeps a backup inside the tool in case the
experiment folder is lost, and a copy inside the experiment folder in case the
tool's internal data is lost.

1. A `jlt_log_<experiment_name>` folder created **next to** the experiment
   folder.
2. A `<experiment_name>` folder created **inside** the tool's configuration
   directory.

Both folders start with :

- `summary_log.md` — a per-experiment summary (initially `"No experiment has
  been executed yet"`);
- `readme.md` — a short description of the folder.

The internal folder additionally stores `info.json`, the registry entry holding
the experiment path, metric name and optimisation direction.

The configuration directory is the same one used by the
[backend subsystem](backend.md#where-configs-are-stored) and is resolved through
`JLT_CONFIG_DIR` / `XDG_CONFIG_HOME` / `~/.config/jlt` :

```
<config_dir>/
    autoresearch/
        experiments/
            <experiment_name>/
                info.json       ---> registry entry (path, metric, direction, ...)
                summary_log.md  ---> backup of the per-experiment summary log
                readme.md       ---> short description of the folder
```

## Python implementation

The autoresearch code lives under `src/jlt/autoresearch/`.

```
src/jlt/autoresearch/
    cli.py                  ---> the `jlt autoresearch` command (subcommand wiring)
    manage/
        experiments.py      ---> public API : add / list / remove (orchestration)
        registry.py         ---> on-disk storage of the registered experiments
        validation.py       ---> static (ast-based) checks of an experiment folder
    run/
        runner.py           ---> experiment execution (still a stub)
```

The registry reuses two helpers from the backend subsystem to avoid duplicating
logic : `get_config_dir` (the JLT configuration root) and the `toml`/`json` IO
helpers from `config_io`. Importing them does not pull any provider SDK, since
those are imported lazily inside each backend.
