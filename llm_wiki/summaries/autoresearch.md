# Autoresearch Subsystem Summary

The **autoresearch** tool is a CLI take on the *autoresearch* idea : the user
registers an experiment, and `autoresearch` will (in a later iteration)
iteratively let an LLM tweak the experiment setup, run it, and analyse the
results in order to optimise a numeric metric.

This document covers the commands implemented today : `add`, `list`, `remove`,
`run` and `sync`. `run` performs **one optimisation round** per invocation
(reading the logs, letting the LLM tweak the config, executing the experiment,
recording the metric and updating the logs) ; looping over many rounds until a
convergence criterion is met is still future work.

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
jlt autoresearch run    --experiment_name <name>           # run one optimisation round
jlt autoresearch sync   [--experiment_name <name>] [--reverse]   # log folder <-> internal backup
```

`autoresearch` can also be abbreviated as `ar`.

- `--ascending` maximises the metric, `--descending` minimises it. Exactly one
  is required and they cannot be combined.
- `--experiment_info_path` points to a `json`/`toml` file holding all the fields
  above (`path_folder`, `metric_name`, `ascending`/`descending`,
  `experiment_name`). When used, no other flag can be passed.
- `remove` only deletes the registry entry : the original experiment folder and
  the `jlt_log_<experiment_name>` folder next to it are left untouched.
- `run` performs **one round** : it needs an active LLM backend (see the
  [backend tool](backend.md)) and produces a `round_<i>.md` log, appends the
  metric to `metrics.csv`/`metrics.txt`, updates `summary_log.md`, increments
  `round.txt` and syncs everything to the internal backup. The experiment code is
  never modified — only the files in its `config` folder.
- `sync` copies the results between the `jlt_log_<name>` folder and the internal
  backup. `--experiment_name` defaults to the current folder name ; `--reverse`
  restores from the backup into the experiment folder. It never deletes files and
  never overwrites the internal `info.json`.

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

# Run one optimisation round (needs an active backend)
jlt ar run --experiment_name my_experiment

# Manually back up / restore the results
jlt ar sync --experiment_name my_experiment              # log folder -> internal backup
jlt ar sync --experiment_name my_experiment --reverse    # internal backup -> log folder
```

A complete, runnable example experiment (training a PyTorch network on a combined
FashionMNIST + KMNIST + EMNIST + CIFAR10 dataset) lives in
[`examples/autoresearch_nn/`](../../examples/autoresearch_nn/).

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
- `round.txt` — the round counter (initially `0`).

The internal folder additionally stores `info.json`, the registry entry holding
the experiment path, metric name and optimisation direction.

Each `run` round then adds (and the final `sync` mirrors into the internal
backup) a `round_<i>.md` log, the metric files `metrics.csv` / `metrics.txt`, and
an updated `summary_log.md`. `info.json` is never synced.

The configuration directory is the same one used by every other JLT tool (e.g.
the [backend subsystem](backend.md#where-configs-are-stored)) and is resolved
through `JLT_CONFIG_DIR` / `XDG_CONFIG_HOME` / `~/.config/jlt` :

```
<config_dir>/
    autoresearch/
        experiments/
            <experiment_name>/
                info.json       ---> registry entry (path, metric, direction, ...)
                summary_log.md  ---> backup of the per-experiment summary log
                readme.md       ---> short description of the folder
                round.txt       ---> round counter (created at add time, =0)
                round_<i>.md    ---> per-round log (synced from a run)
                metrics.csv     ---> metric per round (synced from a run)
                metrics.txt     ---> human-readable metric log (synced from a run)
```

## Python implementation

The autoresearch code lives under `src/jlt/autoresearch/` : `cli.py` wires the
subcommands, `manage/` handles experiment registration (`add` / `list` /
`remove`, plus folder validation and on-disk storage) and `run/` handles
execution (`run` and `sync`). It reuses the shared helpers under
`src/jlt/shared_knowledge/` (`config_io`, `paths`, `backend`).

For a module-by-module walkthrough see the detailed descriptions :

- [`detailed_descriptions/autoresearch_config.md`](../detailed_descriptions/autoresearch_config.md)
  — experiment management (`add` / `list` / `remove`, validation, registry).
- [`detailed_descriptions/autoresearch_run.md`](../detailed_descriptions/autoresearch_run.md)
  — the `run` and `sync` commands.
- [`detailed_descriptions/shared_knowledge.md`](../detailed_descriptions/shared_knowledge.md)
  — code shared across tools.
