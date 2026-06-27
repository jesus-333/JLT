# `autoresearch` experiment management — how it works

This document explains, in depth, how the experiment-management commands of the
`autoresearch` tool are implemented : `add`, `list`/`ls`, `remove`/`rm`, the
folder validation they rely on, and where everything is stored on disk. It is the
technical companion of [`autoresearch_run.md`](autoresearch_run.md) (which covers
`run` and `sync`) and is self-contained.

For the user-facing reference (flags, examples) see
[`summaries/autoresearch.md`](../summaries/autoresearch.md). For the original
specification see
[`instructions/autoresearch/1_config_experiment_ENG.md`](../instructions/autoresearch/1_config_experiment_ENG.md).

## Index

- [What is an experiment](#what-is-an-experiment)
- [`add`](#add)
- [Experiment folder validation](#experiment-folder-validation)
- [`list` / `remove`](#list--remove)
- [The registry and storage layout](#the-registry-and-storage-layout)
- [Module map](#module-map)
- [Notes and provisional choices](#notes-and-provisional-choices)

## What is an experiment

An experiment is a folder containing the scripts that do the actual work (numerical
simulations, neural-network training, ...). Registering it does **not** copy the files :
only the path to the folder, plus a little metadata, is stored internally. Each
experiment is saved under a **name** (defaulting to the folder name).

A valid experiment folder must contain :

- a `config` sub-folder holding the configuration files (`toml` / `json`), which are the
  only thing `run` is allowed to modify ;
- a `run.py` script exposing a top-level `run` function that returns the numeric metric to
  optimise ;
- an `experiment_description.txt` or `.md` describing what the experiment does.

## `add`

`jlt autoresearch add` registers an experiment. It accepts the fields in **two mutually
exclusive ways** :

- the individual flags `--path_folder`, `--metric_name`, `--ascending`/`--descending` and
  the optional `--experiment_name` ; or
- a single `--experiment_info_path` pointing to a `json`/`toml` file holding all those
  fields. When this is used, no other flag may be passed.

Exactly one of `--ascending` (maximise) / `--descending` (minimise) is required. The flag
combinations are checked in [`cli.py`](../../src/jlt/autoresearch/cli.py)
(`_ensure_no_conflicting_flags`, `_ensure_required_add_flags`) before any work is done.

The orchestration lives in
[`manage/experiments.py`](../../src/jlt/autoresearch/manage/experiments.py)
(`add_experiment`, and `add_experiment_from_info_file` for the file mode). It :

1. resolves `path_folder` to an **absolute** path (so the experiment is found regardless of
   the working directory later) and validates the folder (see below) ;
2. resolves the experiment name (defaulting to the folder name) and **refuses to overwrite**
   an existing registration — the user must `remove` first ;
3. creates the external log folder `jlt_log_<name>` next to the experiment, populated with
   `summary_log.md` (a placeholder), `readme.md` and `round.txt` (=`0`) by
   `_create_log_folder` ;
4. writes the registry entry `info.json` and mirrors the same log files into the tool's
   internal backup folder (a second `_create_log_folder` call).

`_create_log_folder` never overwrites existing files, so calling it on an already-populated
folder is safe.

## Experiment folder validation

[`manage/validation.py`](../../src/jlt/autoresearch/manage/validation.py)
(`validate_experiment_folder`) checks the folder **statically** — `run.py` is parsed with
the `ast` module, **never imported or executed** at registration time (it is executed only
later, by `run` ; see [`autoresearch_run.md`](autoresearch_run.md#experiment-execution)).
The checks :

- the folder exists and contains a `config/` sub-folder ;
- an `experiment_description.txt`/`.md` is present ;
- `run.py` exists, defines a **top-level** `run` function, and that function returns a value
  (a bare `return`/`return None` does not count ; returns inside nested functions are
  ignored) ;
- the `run` return annotation is classified : a recognised **numeric** annotation (incl.
  aliases like `np.float64`, `int32`, matched by prefix) passes silently ; a recognised
  **non-numeric** one (`str`, `list`, ...) raises ; a **missing or unclassifiable**
  annotation (`float | None`, generics, none) emits a warning and is accepted.

The last point follows the repo convention "when a static check cannot be certain, warn and
proceed rather than hard-failing valid code".

## `list` / `remove`

- `list` / `ls` returns the registered experiment names (the sub-folders of the internal
  `experiments/` directory that contain an `info.json`).
- `remove` / `rm` deletes **only** the internal registry folder for the experiment. The
  user's experiment folder and the `jlt_log_<name>` folder next to it are intentionally left
  untouched — removing a registration is not a destructive operation on the user's data.

## The registry and storage layout

[`manage/registry.py`](../../src/jlt/autoresearch/manage/registry.py) owns the on-disk
storage. An experiment's information is deliberately kept in **two** places so a copy
survives if either is lost :

```
<config_dir>/autoresearch/experiments/<name>/   ---> internal registry + backup
    info.json       ---> registry entry (path, metric, direction, log_folder)
    summary_log.md  readme.md  round.txt
    metrics.csv  metrics.txt                      (added/synced by `run`)
    round_<i>_backup/                             (one per round, synced by `run`)
        round_<i>.md                              the round log
        config/<files>                            config snapshot used that round
<experiment_parent>/jlt_log_<name>/              ---> copy next to the experiment
    summary_log.md  readme.md  round.txt
    metrics.csv  metrics.txt                      (produced by `run`)
    round_<i>_backup/                             (one per round)
        round_<i>.md
        config/<files>
```

`info.json` is JSON written sorted (via the shared `config_io`) and currently stores
`experiment_name`, `path_folder`, `metric_name`, `optimization_direction`
(`"ascending"`/`"descending"`) and `log_folder`. It is registry metadata and is **never**
synced between the two copies (see
[`autoresearch_run.md`](autoresearch_run.md#sync)).

`<config_dir>` is the shared JLT configuration root, resolved by `get_config_dir` in
`shared_knowledge/paths.py` as `JLT_CONFIG_DIR` → `$XDG_CONFIG_HOME/jlt` → `~/.config/jlt`
(the same root every JLT tool uses ; see [`shared_knowledge.md`](shared_knowledge.md)).

## Module map

The management code lives under `src/jlt/autoresearch/manage/` :

| Module | Purpose |
| --- | --- |
| `experiments.py` | Public API : `add` / `add_from_info_file` / `list` / `remove` (orchestration) + log-folder creation. |
| `registry.py` | On-disk storage : path helpers, list/exists, read/save `info.json`, remove. |
| `validation.py` | Static (`ast`-based) checks of an experiment folder and its `run.py`. |

The CLI wiring for every subcommand lives in `src/jlt/autoresearch/cli.py`.

## Notes and provisional choices

- **The registry format is provisional** : the on-disk schema (`info.json` fields, folder
  layout) may change as the tool evolves.
- **Duplicate experiment names raise an error** — the user must `remove` first. This could
  become an explicit update/overwrite in the future if desired.
- **The numeric-annotation check is intentionally lenient** : it only errors on annotations
  it can positively classify as non-numeric, and warns (rather than fails) on anything it
  cannot classify.
