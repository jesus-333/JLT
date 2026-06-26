# LLM — Start Here

If you are an LLM helping with this repository, read these two files first to
understand the project structure and conventions:

- [`llm_wiki/index.md`](llm_wiki/index.md) — wiki entry point / map.
- [`llm_wiki/summaries/general_info.md`](llm_wiki/summaries/general_info.md) —
  project purpose, CLI usage and repository structure.

## Coding style e convention

When writing or modifying code in this repository, follow the style rules described in [`coding_and_style_instructions_ENG.md`](./llm_wiki/instructions/generic_instruction/coding_style_instructions_ENG.md).
That file is the single source of truth for the coding style and is kept separate from this summary so it can be updated independently.

Furthermore the file [`coding_convention_istructions.md`](./llm_wiki/instructions/generic_instruction/coding_convention_istructions.md) has some convention to follow.

## Conventions for the wiki folders

- `llm_wiki/instructions/` — files written by the maintainer describing new tasks and stuff to implement.
- `llm_wiki/detailed_descriptions/` — detailed descriptions of how the code and repository work (populated over time). Per-tool progress/roadmap files live here too, named `<tool>_status.md` (e.g. `detailed_descriptions/autoresearch_status.md`).
- `llm_wiki/dump/` — scratch folder. If, while implementing features/code, you need to create temporary description files, TODO lists, notes, etc., put them here.

## Environment setup

A fresh clone is **not** installed. Before running or testing anything:

```bash
pip install -e .[all-backends]   # or just `pip install -e .` for the core CLI
```

Individual backends have their own extras (e.g. `.[claude]`, `.[ollama]`).
Run the CLI through the `jlt` entry point (`jlt autoresearch ls`) or `python -m jlt.cli`.

There is **no test suite yet**. Until one exists, validate CLI changes by driving the command against a throwaway config directory so you never touch real user data
