# JLT Wiki — Index

Entry point for the **Jesus's LLM Tools (JLT)** wiki. Start here to navigate the documentation.

## Summaries

- [`summaries/general_info.md`](summaries/general_info.md) — High-level overview: project purpose, CLI usage, repository structure and coding-style pointer.
- [`summaries/backend.md`](summaries/backend.md) — Summary of the shared backend subpackage (`src/jlt/shared_knowledge/backend`).
- [`summaries/autoresearch.md`](summaries/autoresearch.md) — Summary of the `autoresearch` tool (`src/jlt/autoresearch`): experiment configuration commands (`add`/`list`/`remove`).

## Instructions

Files written by the maintainer describing new tasks and stuff to implement.

- [`instructions/generic_instruction/codying_and_style_instructions_ENG.md`](instructions/generic_instruction/codying_and_style_instructions_ENG.md) — Single source of truth for coding style.
- [`instructions/generic_instruction/file_writing.md`](instructions/generic_instruction/file_writing.md) — Request for a backend `write_file` helper (implemented as `generic_backend.write_file`).
- [`instructions/generic_instruction/repo_setup_ENG.md`](instructions/generic_instruction/repo_setup_ENG.md) — Repository setup instructions.
- [`instructions/backend/0_general_backend_setup_ENG.md`](instructions/backend/0_general_backend_setup_ENG.md) — Backend setup instructions.
- `instructions/0_original_IT_files/` — Original Italian versions of the instruction files. Can be ignored.

## Detailed descriptions

- [`detailed_descriptions/`](detailed_descriptions/) — In-depth explanations of how the code and the repository work. To be populated over time. Separate from `instructions/`.

## Dump

- [`dump/`](dump/) — Scratch folder for work-in-progress files. When implementing new features/code, put any temporary description files, TODO lists, notes, etc. here.

## Quick map of the repository

```
llm_wiki/      ---> this wiki
scripts_sh/    ---> shell scripts (future use)
src/jlt/       ---> all JLT source code (cli.py + one subpackage per tool)
tutorial/      ---> old folder, can be ignored
```

For the full structure and explanation, see
[`summaries/general_info.md`](summaries/general_info.md).
