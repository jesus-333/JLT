# `autoresearch` — Current Status

This document tracks **what is implemented and what is still pending** in the
`autoresearch` tool. It is a living status/roadmap file : update it whenever a
component moves from "planned" to "done".

For a user-facing reference of the commands that already work, see
[`summaries/autoresearch.md`](../summaries/autoresearch.md). For the original
specifications, see
[`instructions/autoresearch/`](../instructions/autoresearch/).

_Last updated : 2026-06-26 — after implementing the experiment-configuration
commands (`add` / `list` / `remove`)._

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
| CLI structure (all subcommands wired) | ✅ Done | `add`, `list`/`ls`, `remove`/`rm`, `run` all parse and dispatch. |
| `add` | ✅ Done | Folder validation + registration + log folders. |
| `list` / `ls` | ✅ Done | Lists registered experiment names. |
| `remove` / `rm` | ✅ Done | Removes the registry entry only (keeps user files). |
| `run` | ⛔ Stub | Raises `NotImplementedError`. The whole optimisation loop is future work. |
| Per-round logs (`round_i.md`) | ⛔ Not started | Produced by `run`; spec known, intentionally deferred. |
| Per-round metric tracking (`csv` + `txt`) | ⛔ Not started | Produced by `run`. |
| Daily `summary_log.md` updates | 🟡 Partial | The file is *created* at `add` time (placeholder text); it is not yet *updated* (that happens in `run`). |
| Convergence criterion / final report | ⛔ Not started | Deferred. |
| LLM / backend integration | ⛔ Not started | `run` will use `jlt.shared_knowledge.backend.load_backend`. |

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
    info.json  summary_log.md  readme.md
<experiment_parent>/jlt_log_<name>/              ---> copy next to the experiment
    summary_log.md  readme.md
```

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
        __init__.py         ✅ re-exports run_experiment
        runner.py           ⛔ run_experiment is a stub (NotImplementedError)
```

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
- **`run` not designed yet.** When implemented it must : execute `run.py`'s
  `run` function, append the metric to per-round `csv`/`txt` files, write
  `round_i.md` logs, update `summary_log.md`, and keep both storage copies in
  sync.
```
