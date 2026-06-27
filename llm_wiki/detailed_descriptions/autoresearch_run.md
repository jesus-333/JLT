# `autoresearch run` and `sync` — how they work

This document explains, in depth, how the `run` and `sync` commands of the
`autoresearch` tool are implemented. It is meant to be the authoritative technical
reference for these two commands and is self-contained : it does not rely on the
status/roadmap file ([`autoresearch_status.md`](autoresearch_status.md)).

For the user-facing reference (flags, examples, storage layout) see
[`summaries/autoresearch.md`](../summaries/autoresearch.md). For the original
specification see
[`instructions/autoresearch/2_run_experiment_ENG.md`](../instructions/autoresearch/2_run_experiment_ENG.md).

## Index

- [Overview](#overview)
- [Prerequisites and inputs](#prerequisites-and-inputs)
- [The per-round sequence](#the-per-round-sequence)
- [Conversation memory](#conversation-memory)
- [The "read previous rounds ?" exchange](#the-read-previous-rounds-exchange)
- [The `round_<i>.md` lifecycle](#the-round_imd-lifecycle)
- [Safe configuration update](#safe-configuration-update)
- [Experiment execution](#experiment-execution)
- [Metric tracking](#metric-tracking)
- [`summary_log.md` update](#summary_logmd-update)
- [The round counter](#the-round-counter)
- [Sync](#sync)
- [Failure semantics](#failure-semantics)
- [Module map](#module-map)
- [Limitations and future work](#limitations-and-future-work)

## Overview

`jlt autoresearch run --experiment_name <name>` performs **exactly one optimisation
round** of a registered experiment. A round is the cycle in which an LLM looks at the
results so far, decides how to tweak the experiment hyperparameters, the experiment is
executed, and the LLM analyses the outcome.

Two invariants hold throughout :

- The experiment **code is never modified** — only the files inside the experiment
  `config` folder are.
- The experiment is **launched programmatically** by `autoresearch` (by calling
  `run.py`'s `run` function), never by the LLM.

`run` needs an **active LLM backend** (configured through the separate `backend` tool,
see [`summaries/backend.md`](../summaries/backend.md)). Running it repeatedly accumulates
one `round_<i>.md` log and one metric row per invocation.

## Prerequisites and inputs

`run` expects an experiment that was registered with `jlt autoresearch add` and therefore
has :

- an internal registry entry `info.json` holding `path_folder`, `metric_name`,
  `optimization_direction` and `log_folder` ;
- the external `jlt_log_<name>` folder next to the experiment, containing `summary_log.md`,
  `readme.md` and `round.txt` (the latter created `=0` at registration time) ;
- inside the experiment folder : the mandatory `experiment_description.txt`/`.md`, a
  `config` sub-folder and a `run.py` exposing a numeric `run` function.

## The per-round sequence

`run_experiment(experiment_name)` in
[`run/runner.py`](../../src/jlt/autoresearch/run/runner.py) orchestrates the round. The
ordered steps, with the code responsible for each :

1. Read the registry entry — `registry.read_experiment_info`. Resolve `path_folder`,
   `log_folder`, `config_dir`, `metric_name`, `direction` ; load the active backend
   (`load_backend`) and create the round context.
2. Read the mandatory `experiment_description.*` (`_load_description`) and add it to the
   context.
3. Read the current round number `i` — `round_io.read_round` ; create the per-round folder
   `round_<i>_backup/` and write `round_<i>.md` **inside** it from the internal template ;
   read `summary_log.md` and add it to the context.
4. Optionally read previous round reports — `_maybe_read_previous_rounds` (the interactive
   yes/no + file-list exchange).
5. Let the LLM write the *Summary Previous Rounds* and *Experiment Configuration Update*
   sections of `round_<i>.md` (`context.ask`, then `_write_round_file`).
6. Apply the configuration changes — `config_update.update_all_configs` — then snapshot the
   modified config into `round_<i>_backup/config/` — `_backup_round_configs`.
7. Run the experiment — `experiment_runner.run_experiment_script`, returning the numeric
   metric.
8. Append the metric — `metrics_io.append_metric`.
9. Let the LLM write the *Result and analysis* section of `round_<i>.md`.
10. Rewrite `summary_log.md` to incorporate the round — `_update_summary_log`.
11. Increment the round counter — `round_io.increment_round`.
12. **Last step** : back everything up — `sync_experiment(experiment_name)`.

## Conversation memory

The specification requires that all steps of one round happen "within the same LLM
conversation, so that information is kept in memory". The JLT backends are intentionally
**stateless** : each `generic_backend._chat` call is independent and carries no history.

Rather than rewrite every backend to support multi-turn sessions, the conversation is
**simulated** by [`run/conversation.py`](../../src/jlt/autoresearch/run/conversation.py).
The `round_context` class keeps an in-memory transcript and forwards it into every call :

- `add(label, text)` appends a labelled block (the description, the summary log, a previous
  report, an earlier exchange) to the transcript ;
- `ask(prompt, system=None)` prepends the whole transcript to `prompt`, sends it through the
  backend's public `chat()` method, then records both the question and the answer so later
  questions can refer back to them ;
- `render()` returns the transcript as a single string (used when an instruction string —
  e.g. for `modify_file` — must carry the round context).

`chat()` is a one-line public passthrough to `_chat` added on `generic_backend` so the
runner never reaches into the "private" primitive. The backend stays stateless ; the memory
lives entirely in `round_context`.

## The "read previous rounds ?" exchange

After the description and the summary log are in the context, `_maybe_read_previous_rounds`
runs the optional protocol from the spec :

1. If there are no previous `round_*.md` reports, it returns immediately.
2. Otherwise the LLM is asked, strictly yes or no, whether it wants to read any. The answer
   is interpreted by `_parse_yes_no` (affirmative if it starts with `y`; anything else,
   including an empty answer, is treated as "no" — the safe default).
3. If yes, the LLM is given the list of available filenames and asked to reply with a
   comma-separated list of the ones it wants. `_parse_file_list` splits on commas/newlines
   and keeps **only filenames that actually exist** (intersection with the real list), so a
   hallucinated or malformed name is silently dropped.
4. The chosen files are read together with `backend.read_files` and added to the context.

## The per-round backup folder (`round_<i>_backup/`)

Every round owns a folder `jlt_log_<name>/round_<i>_backup/`, created at the start of the
round, that makes the round **reproducible** : it gathers the round's log and a snapshot of the
exact config that produced its result. Its content :

- `round_<i>.md` — the round log (it lives here, **not** at the top level of the log folder) ;
- `config/<files>` — a copy of the experiment's config files **as modified for this round**,
  written by `_backup_round_configs` right after `update_all_configs`. The `config/` layout is
  preserved, so the snapshot is a drop-in replacement for the experiment's own `config/` folder.

The cumulative artifacts (`summary_log.md`, `metrics.csv`, `metrics.txt`, `round.txt`) stay at
the top level of `jlt_log_<name>/` ; only the per-round log and config snapshot live in the
backup folder. The whole `round_<i>_backup/` tree is mirrored into the internal backup by the
final sync (see [Sync](#sync)).

## The `round_<i>.md` lifecycle

The per-round log template lives as a module-level string in
[`run/round_template.py`](../../src/jlt/autoresearch/run/round_template.py) (a string
constant rather than a data file, so it always ships with the package). It contains three
sections, matched verbatim by the runner :

```
# Summary Previous Rounds
# Experiment Configuration Update
# Result and analysis
```

At the start of the round the template is written verbatim to `round_<i>_backup/round_<i>.md`
(so the file exists in its canonical empty form even if a later step fails). As the round
progresses the file is **rebuilt from the captured section texts** (`_write_round_file`) rather
than patched in place : rebuilding guarantees the three headers always stay present and in
order, even on a partial round. The *Summary* and *Configuration Update* sections are filled in
step 5, the *Result and analysis* section in step 9.

The "read previous rounds" step (`_list_previous_round_files`) therefore looks one level down,
globbing `round_*_backup/round_*.md`, to find earlier round logs.

## Safe configuration update

Letting an LLM rewrite a structured config file is error prone, so
[`run/config_update.py`](../../src/jlt/autoresearch/run/config_update.py) makes it robust.
`update_all_configs` iterates over every `.json`/`.toml` file in the `config` folder
(`list_config_files`) and calls `apply_config_update` on each. For a single file :

1. Snapshot the original raw text and the original set of **key-paths**
   (`_collect_key_paths`, which recurses into nested dicts and records each key as the tuple
   of keys leading to it).
2. Rewrite the file with `backend.modify_file`, passing instructions that combine the round's
   configuration decision with a reminder to only change values, never add/remove/rename keys.
3. Re-parse the file (`read_config_file`) and compare its key-paths against the snapshot.
4. If the keys match, the update succeeded (values may have changed; the set of
   hyperparameters did not). If they differ, or the file can no longer be parsed, restore the
   original text and retry.

Retries are capped at `MAX_CONFIG_RETRIES` (3) ; after that a `RuntimeError` is raised and the
original content is restored. Only the **keys** are compared — the whole point of a round is to
change values. Both `.json` and `.toml` configs are supported (writing `.toml` is possible
thanks to the TOML writer added to the shared `config_io`; see
[`shared_knowledge.md`](shared_knowledge.md)).

## Experiment execution

[`run/experiment_runner.py`](../../src/jlt/autoresearch/run/experiment_runner.py) runs the
experiment. Whereas registration validates `run.py` **statically** (the script is parsed with
`ast`, never imported), `run_experiment_script` actually executes it :

- it builds an import spec with `importlib.util.spec_from_file_location` and executes the
  module ;
- the experiment folder is prepended to `sys.path` for the import (so `run.py` can import its
  own sibling modules) and removed afterwards ; the temporary module is also dropped from
  `sys.modules` ;
- `run()` is called from **inside the experiment folder** (a `_working_directory` context
  manager `os.chdir`s in and always restores the previous cwd), so the experiment's relative
  paths to its config / data / outputs keep working ;
- the result is coerced with `float(...)`. A missing/non-callable `run`, an exception raised by
  the experiment, or a non-numeric result are all wrapped in a clear `RuntimeError`.

## Metric tracking

[`run/metrics_io.py`](../../src/jlt/autoresearch/run/metrics_io.py) appends the round's metric
to two files in the log folder (`append_metric`) :

- `metrics.csv` — machine readable, header `round,<metric_name>` written only when the file is
  first created, then one row per round ;
- `metrics.txt` — human readable, one `round <i> : <metric_name> = <value>` line per round.

Both files are appended to, never rewritten, so the full cross-round history is preserved.

## `summary_log.md` update

After the metric is known, `_update_summary_log` rewrites `summary_log.md` with
`backend.modify_file`. The instructions embed the round context (`context.render()`) plus the
new round number, metric value and optimisation direction, and ask the model to produce a
concise **cumulative** summary of all rounds so far (keeping the previous rounds' information).

## The round counter

[`run/round_io.py`](../../src/jlt/autoresearch/run/round_io.py) owns `round.txt`. The file
holds a single integer and is created `=0` at registration time (by
`manage.experiments._create_log_folder`, which reuses the `ROUND_FILE_NAME` constant defined
there). `read_round` parses it (a malformed counter is a hard error, never silently reset),
`write_round` overwrites it and `increment_round` bumps it by one. The increment happens as the
penultimate step of a round, so a round number is only consumed once the round has actually
completed.

## Sync

[`run/sync.py`](../../src/jlt/autoresearch/run/sync.py) keeps the two copies of an
experiment's results in step. Each experiment has its logs in two places : the external
`jlt_log_<name>` folder next to the experiment, and the internal backup folder
`registry.get_experiment_dir(name)` inside the JLT config directory.

`sync_experiment(experiment_name=None, reverse=False)` :

- defaults `experiment_name` to the current folder name when `None` (matching the `add`
  default), then resolves both endpoints from the registry ;
- copies the external folder into the internal backup by default (this is step 12 of a round),
  or the internal backup into the external folder when `reverse=True` (a restore) ;
- copies **recursively** : `_copy_log_files` mirrors sub-folders too, so each
  `round_<i>_backup/` (with its `round_<i>.md` and `config/` snapshot) is synced together with
  the top-level cumulative files ;
- is **copy only** : it overwrites/creates files at the destination but never deletes, and it
  **skips `info.json`** (only at the top level, where the registry entry lives) so the registry
  metadata is never clobbered by a log sync.

The same logic is exposed on the command line as `jlt autoresearch sync`
(`--experiment_name`, `--reverse`).

## Failure semantics

Errors are raised **before** the round counter is incremented and before the sync, so a failed
round leaves `round.txt` untouched : the next `run` reuses the same round number (overwriting
the partial `round_<i>.md`). A partial `round_<i>.md` may remain on disk, which is useful for
debugging. The two most common failures are a configuration update that cannot keep the keys
intact (after 3 retries) and an experiment `run` that raises or returns a non-numeric value ;
both surface as a `RuntimeError`, which the CLI entry point turns into an
`Error while running experiment ... : <error>` message and a non-zero exit code.

## Module map

All `run`-specific code lives under `src/jlt/autoresearch/run/` :

| Module | Purpose |
| --- | --- |
| `runner.py` | `run_experiment` : orchestrates one round (the 12 steps above). |
| `round_io.py` | Read / write / increment `round.txt`. |
| `round_template.py` | The internal `round_<i>.md` template (string constant). |
| `conversation.py` | `round_context` (forwarded transcript) + the yes/no & file-list parsers. |
| `config_update.py` | Safe config edits : backup + recursive key-path check + retries. |
| `experiment_runner.py` | Dynamic import and execution of `run.py`'s `run()`. |
| `metrics_io.py` | Append the metric to `metrics.csv` / `metrics.txt`. |
| `sync.py` | `sync_experiment` : log folder ↔ internal backup. |

## Limitations and future work

- **One round per invocation.** Looping over many rounds, a convergence criterion and a final
  report are deliberately not implemented yet ; each `run` does a single round.
- **Conversation memory is simulated**, not a true multi-turn session : the runner forwards a
  growing transcript into a stateless backend.
- The configuration update trusts the LLM to keep the file format valid ; the safety net is the
  key-path comparison and the retry/restore loop, not a schema.
