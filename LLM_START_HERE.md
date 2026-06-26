# LLM — Start Here

If you are an LLM helping with this repository, read these two files first to
understand the project structure and conventions:

- [`llm_wiki/index.md`](llm_wiki/index.md) — wiki entry point / map.
- [`llm_wiki/summaries/general_info.md`](llm_wiki/summaries/general_info.md) —
  project purpose, CLI usage and repository structure.

## Coding Style

When writing or modifying code in this repository, follow the conventions described in [`codying_and_style_instructions_ENG.md`](./llm_wiki/instructions/generic_instruction/codying_and_style_instructions_ENG.md).
That file is the single source of truth for the coding style and is kept separate from this summary so it can be updated independently.

## Conventions for the wiki folders

- `llm_wiki/instructions/` — files written by the maintainer describing new tasks
  and stuff to implement.
- `llm_wiki/detailed_descriptions/` — detailed descriptions of how the code and
  repository work (populated over time). Per-tool progress/roadmap files live
  here too, named `<tool>_status.md` (e.g.
  `detailed_descriptions/autoresearch_status.md`).
- `llm_wiki/dump/` — scratch folder. If, while implementing features/code, you
  need to create temporary description files, TODO lists, notes, etc., put them
  here.

## Environment setup

A fresh clone is **not** installed. Before running or testing anything:

```bash
pip install -e .[all-backends]   # or just `pip install -e .` for the core CLI
```

Individual backends have their own extras (e.g. `.[claude]`, `.[ollama]`).
Run the CLI through the `jlt` entry point (`jlt autoresearch ls`) or
`python -m jlt.cli`.

There is **no test suite yet**. Until one exists, validate CLI changes by
driving the command against a throwaway config directory so you never touch real
user data:

```bash
JLT_CONFIG_DIR=$(mktemp -d) jlt autoresearch add --path_folder ./some_exp --metric_name acc --ascending
```

## Coding conventions & defaults

Beyond the style guide, the codebase follows the conventions below. They are
defaults, not laws — if you want one changed, tell me rather than letting me
guess differently each time.

- **CLI entry points** return an `int` exit code, wrap the work in `try/except`,
  print `Error while <action> : <error>` and return `1` on failure, and print a
  success line and return `0` otherwise. See `backend/cli.py` and
  `autoresearch/cli.py`.
- **Prefer erroring over silent destructive actions.** E.g. `autoresearch add`
  refuses to overwrite an existing registry entry — the user must `remove`
  first. (Contrast with `backend config`, which is intentionally a
  create-or-update.)
- **Store absolute, resolved paths internally**, not the path as typed by the
  user (so the tool keeps working regardless of the current directory later).
- **When a static check cannot be certain, warn and proceed** rather than
  hard-failing valid code; only raise an error for cases you can positively
  classify as wrong. Example: the numeric-return check in
  `autoresearch/manage/validation.py` accepts recognised numeric annotations,
  errors on recognised non-numeric ones (`str`, `list`, …), and merely *warns*
  on annotations it cannot classify (`float | None`, generics, missing).
- **Registry / metadata files** are JSON written sorted (via the shared
  `config_io`). Their on-disk schema is provisional and may change as the tools
  evolve.

## Shared code & per-tool data layout

- Code reused across tools lives **directly** under `src/jlt/shared_knowledge/`,
  not inside any specific tool, so a tool never has to import another tool's
  package. The generic helpers there are `shared_knowledge/paths.py`
  (`get_config_dir`, the JLT config root) and `shared_knowledge/config_io.py`
  (toml/json read, json write); both the `backend` and `autoresearch` tools
  import them. When you write a new genuinely-shared helper, put it here (a new
  module if it doesn't fit an existing one) rather than nesting it under a tool.
- The JLT config directory is shared by all tools and resolved via
  `JLT_CONFIG_DIR` → `XDG_CONFIG_HOME/jlt` → `~/.config/jlt`. **Each tool
  namespaces its own data under `<config_dir>/<tool_name>/`** (e.g.
  `autoresearch/`). The `backend` tool is the historical exception: it writes
  `active.json` and `backends/` directly at the config-dir root. Keep new tools
  namespaced to avoid filename collisions.
