# JLT Wiki — Index

Entry point for the **Jesus's LLM Tools (JLT)** wiki. Start here to navigate the documentation.

## Summaries

- [`summaries/general_info.md`](summaries/general_info.md) — High-level overview: project purpose, CLI usage, repository structure and coding-style pointer.
- [`summaries/backend.md`](summaries/backend.md) — Summary of the shared backend subpackage (`src/jlt/shared_knowledge/backend`).
- [`summaries/autoresearch.md`](summaries/autoresearch.md) — Summary of the `autoresearch` tool (`src/jlt/autoresearch`): the `add`/`list`/`remove`/`run`/`sync` commands.

## Instructions

Files written by the maintainer describing new tasks and stuff to implement.

- [`instructions/generic_instruction/coding_style_instructions_ENG.md`](instructions/generic_instruction/coding_style_instructions_ENG.md) — Single source of truth for coding style.
- [`instructions/generic_instruction/coding_convention_istructions.md`](instructions/generic_instruction/coding_convention_istructions.md) — Coding conventions & defaults (CLI shape, error handling, shared-code layout).
- [`instructions/generic_instruction/file_writing.md`](instructions/generic_instruction/file_writing.md) — Request for a backend `write_file` helper (implemented as `generic_backend.write_file`).
- [`instructions/generic_instruction/repo_setup_ENG.md`](instructions/generic_instruction/repo_setup_ENG.md) — Repository setup instructions.
- [`instructions/backend/0_general_backend_setup_ENG.md`](instructions/backend/0_general_backend_setup_ENG.md) — Backend setup instructions.
- `instructions/0_original_IT_files/` — Original Italian versions of the instruction files. Can be ignored.

## Detailed descriptions

In-depth explanations of how the code and the repository work (separate from `instructions/`, populated over time).

- [`detailed_descriptions/autoresearch_status.md`](detailed_descriptions/autoresearch_status.md) — Status / roadmap of the `autoresearch` tool : what is done and what is still pending.
- [`detailed_descriptions/autoresearch_config.md`](detailed_descriptions/autoresearch_config.md) — Technical deep-dive of `autoresearch` experiment management (`add`/`list`/`remove`, validation, registry).
- [`detailed_descriptions/autoresearch_run.md`](detailed_descriptions/autoresearch_run.md) — Technical deep-dive of the `autoresearch` `run` and `sync` commands.
- [`detailed_descriptions/shared_knowledge.md`](detailed_descriptions/shared_knowledge.md) — Code shared across tools (`config_io`, `paths`, `backend`) and the cross-tool touchpoints.

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
