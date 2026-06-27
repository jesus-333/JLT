# `autoresearch` — Current Status

This document tracks **what is implemented and what is still pending** in the
`autoresearch` tool. It is a living status/roadmap file : update it whenever a
component moves from "planned" to "done".

For a user-facing reference of the commands that already work, see
[`summaries/autoresearch.md`](../summaries/autoresearch.md). For the original
specifications, see
[`instructions/autoresearch/`](../instructions/autoresearch/).

_Last updated : 2026-06-27 — after implementing the `run` command (one
optimisation round per invocation) and the companion `sync` command._

## The vision (where this is going)

`autoresearch` is a CLI take on Karpathy's *autoresearch* idea. The intended
end-to-end workflow (see
[`0_general_autoresearch_setup_ENG.md`](../instructions/autoresearch/0_general_autoresearch_setup_ENG.md)) :

0. The user configures an LLM backend (handled by the separate `backend` tool).
1. The user creates the experiment files in a folder and registers it.
2. `autoresearch` inspects the files and any extra user instructions.
3. The optimisation loop (per **round**) :
   1. an LLM modifies the experiment *setup* — **never the experiment code**;
   2. `autoresearch` launches the experiment programmatically (not via the LLM);
   3. the LLM analyses the results and plans the next round;
   4. repeat until a convergence criterion is met.
4. A final report is produced.

## Status at a glance

| Component | Status | Notes |
|---|---|---|
| CLI structure (all subcommands wired) | ✅ Done | `add`, `list`/`ls`, `remove`/`rm`, `run`, `sync` all parse and dispatch. |
| `add` | ✅ Done | Folder validation + registration + log folders (now also creates `round.txt` = `0`). |
| `list` / `ls` | ✅ Done | Lists registered experiment names. |
| `remove` / `rm` | ✅ Done | Removes the registry entry only (keeps user files). |
| `run` | ✅ Done | Runs **one optimisation round** per invocation (see below). |
| `sync` | ✅ Done | Copies the log folder ↔ internal backup (`--reverse` to restore). |
| Round counter (`round.txt`) | ✅ Done | Created at `add` time (=`0`), incremented at the end of each round. |
| Per-round logs (`round_i.md`) | ✅ Done | Built from an internal template; 3 sections filled by the LLM during the round. |
| Per-round metric tracking (`csv` + `txt`) | ✅ Done | `metrics.csv` (`round,<metric_name>`) + human-readable `metrics.txt`. |
| `summary_log.md` updates | ✅ Done | Created at `add` time (placeholder); rewritten by the LLM at the end of each round. |
| Safe config edits (backup + key check) | ✅ Done | Recursive key-path comparison after each edit; retried up to 3× then errors. |
| LLM / backend integration | ✅ Done | `run` uses `jlt.shared_knowledge.backend.load_backend` (stateless backend + forwarded round context). |
| Convergence criterion / final report | ⛔ Not started | Deferred. `run` does one round; looping/stopping is future work. |

## What is implemented (details)

### Commands

- **`add`** — registers an experiment (path saved, files never copied).
  - Two input modes : the individual flags
    (`--path_folder`, `--metric_name`, `--ascending`/`--descending`,
    `--experiment_name`) **or** a single `--experiment_info_path` json/toml
    file. The two modes are mutually exclusive.
  - Exactly one of `--ascending` (maximise) / `--descending` (minimise) is
    required.
  - Validation of the experiment folder (see below).
  - Creates the `jlt_log_<name>` folder next to the experiment **and** a mirror
    inside the tool's config directory, each with `summary_log.md`
    (placeholder) + `readme.md`. The internal folder also holds `info.json`.
- **`list` / `ls`** — prints the registered experiment names.
- **`remove` / `rm`** — deletes the internal registry folder for the experiment;
  the user's experiment folder and its `jlt_log_<name>` folder are left intact.
- **`run`** — runs **one optimisation round**. From inside the experiment folder it :
  1. reads the mandatory `experiment_description.*` and `summary_log.md` ;
  2. creates `round_<i>.md` from the internal template (`i` = current `round.txt`) ;
  3. optionally asks the LLM (yes/no, then which files) to read previous `round_*.md`
     reports for more context ;
  4. lets the LLM write the *Summary Previous Rounds* and *Experiment Configuration
     Update* sections, then applies the config changes safely (backup + recursive
     key-path comparison, retried up to 3× then errors) ;
  5. executes `run.py`'s `run()` programmatically (from the experiment folder),
     captures the numeric metric, appends it to `metrics.csv` / `metrics.txt` ;
  6. lets the LLM write the *Result and analysis* section and rewrites `summary_log.md` ;
  7. increments `round.txt` and, as the **last** step, syncs the log folder into the
     internal backup.
  All the round's LLM calls share one in-memory transcript
  (`run.conversation.round_context`) forwarded into each request, since the backend is
  stateless. The experiment **code** is never modified — only its config files.
- **`sync`** — copies the experiment results between its `jlt_log_<name>` folder and the
  tool's internal backup. `--experiment_name` defaults to the current folder name ;
  `--reverse` copies internal → external (restore). Copy-only (never deletes) and never
  touches the internal `info.json`.

### Experiment folder validation (`manage/validation.py`)

Performed statically — `run.py` is **parsed via `ast`, never imported or
executed** :

- the folder exists;
- a `config/` sub-folder is present;
- a `run.py` script is present, defines a top-level `run` function, and that
  function returns a value;
- the `run` return annotation is checked : recognised numeric → pass; recognised
  non-numeric (e.g. `str`) → error; missing or unclassifiable → warning + accept.

### Storage layout

```
<config_dir>/autoresearch/experiments/<name>/   ---> internal registry + backup
    info.json  summary_log.md  readme.md  round.txt
    round_<i>.md  metrics.csv  metrics.txt        (added/synced by `run`)
<experiment_parent>/jlt_log_<name>/              ---> copy next to the experiment
    summary_log.md  readme.md  round.txt
    round_<i>.md  metrics.csv  metrics.txt        (produced by `run`)
```

`round.txt` is created (=`0`) at `add` time ; the per-round files are produced by `run`
and mirrored into the internal backup by the final `sync` step (`info.json` is never synced).

`<config_dir>` is the shared JLT config dir (`JLT_CONFIG_DIR` /
`XDG_CONFIG_HOME` / `~/.config/jlt`), resolved by
`get_config_dir` in `shared_knowledge/paths.py`.

## Source file map

```
src/jlt/autoresearch/
    cli.py                  ✅ all subcommands wired; add-flag validation
    manage/
        __init__.py         ✅ re-exports the public API
        experiments.py      ✅ add / add_from_info_file / list / remove (orchestration)
        registry.py         ✅ on-disk storage (paths, list, save, read, remove)
        validation.py       ✅ ast-based folder + run.py checks
    run/
        __init__.py         ✅ re-exports run_experiment + sync_experiment
        runner.py           ✅ run_experiment : orchestrates one optimisation round
        round_io.py         ✅ read / write / increment round.txt
        round_template.py   ✅ internal round_<i>.md template (string constant)
        conversation.py     ✅ round_context (forwarded transcript) + answer parsers
        config_update.py    ✅ safe config edits (backup + recursive key check + retries)
        experiment_runner.py✅ dynamic import + execution of run.py's run()
        metrics_io.py       ✅ append metric to metrics.csv / metrics.txt
        sync.py             ✅ sync_experiment : log folder <-> internal backup
```

### Shared-code changes (used by other tools)

Implementing `run` touched two pieces of shared code under `src/jlt/shared_knowledge/`
(flagged here per the repo convention that shared-code changes are reported) :

- `shared_knowledge/config_io.py` — added a **TOML writer** (`_write_toml`, registered in
  `WRITERS`) so config files can be written back in `.toml` as well as `.json`. This pulls
  in the small `tomli-w` package (stdlib `tomllib` reads but cannot write toml), now the
  single **core** dependency in `pyproject.toml`. The import is lazy, matching the
  backend-SDK pattern.
- `shared_knowledge/backend/generic.py` — added a one-line public `chat()` passthrough to
  `_chat` (so the runner drives free-form prompts without touching the private primitive),
  and hardened `modify_file` so a long instruction string no longer crashes the
  "is the prompt a file path?" check (`Path(prompt).is_file()` could raise `OSError`).

## Open questions / decisions to revisit

- **Registry format is provisional.** The instruction notes the registry
  behaviour "may change as work progresses". `info.json` currently stores
  `experiment_name`, `path_folder`, `metric_name`, `optimization_direction`,
  `log_folder`.
- **Duplicate experiment names** currently raise an error (the user must
  `remove` first). Could become an explicit update/overwrite if desired.
- **Numeric-annotation check** uses a prefix heuristic (so `np.float64`,
  `int32`, … pass) and *warns* instead of erroring on annotations it cannot
  classify (e.g. `float | None`, generics). This is more lenient than a strict
  reading of the spec.
- **`run` runs a single round.** Looping over rounds / a convergence criterion /
  a final report are deliberately **not** implemented yet : each `jlt autoresearch
  run` performs exactly one round. Repeated runs accumulate `round_<i>.md` files
  and metric rows.
- **Conversation memory is simulated.** The backend stays stateless ; the runner
  forwards a growing in-memory transcript (`round_context`) into each LLM call
  instead of a true multi-turn session.
- **Config key comparison is recursive.** The set of nested key-paths must match
  before/after an edit ; only values may change. `.toml` and `.json` configs are
  both supported (the latter required adding the TOML writer noted above).
```
