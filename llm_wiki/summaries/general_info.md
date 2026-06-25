# JLT Repository Summary

## Purpose

**Jesus's LLM Tools (JLT)** is a personal Python package collecting a set of tools that make use of Large Language Models (LLMs). Each tool is self-contained and lives in its own subpackage, but all of them are exposed through a single command line entry point.

## CLI Usage

Every tool is invoked from the command line through the shared `jlt` command:

```
jlt <tool_name> <tool_subcommand, tool_variable, tool_flags>
```

Where:
- `jlt` is the acronym for the whole project.
- `<tool_name>` is the name of the specific tool to run.
- the remaining arguments cover all the subcommands, variables and flags of that specific tool.

The top-level parser lives in `src/jlt/cli.py`. Each tool exposes a `register(subparsers)` function in its own `cli` module, which attaches the tool's argument parser (with its subcommands, variables and flags) to the shared top-level parser. 
Adding a new tool is essentially a one-line change in the `TOOLS` list of `src/jlt/cli.py`.

## Repository Structure

```
    llm_wiki/                       ---> "wiki" of the project
        README.md                   ---> Short description of the wiki itself
        index.md                    ---> Entry point / map of the wiki
        instructions/               ---> Files written by the maintainer describing new tasks / stuff to implement
            0_original_IT_files/    ---> Original version of the instructions files (in italian). Can be ignored.
            backend/                ---> Backend-related instructions (English)
            generic_instruction/    ---> Generic coding/style/repo-setup instructions (English)
        detailed_descriptions/      ---> Detailed descriptions of how the code and repository work (to be populated)
        dump/                       ---> Scratch folder for WIP files (temporary descriptions, TODO lists, notes, ...)
        summaries/                  ---> Contains various summaries for the whole project
    scripts_sh/                     ---> Folder for any shell scripts to be used in the future
    src/                            ---> Folder for all the JLT source code
    tutorial/                       ---> Old folder. Can be ignored
    LICENSE
    README.md
    pyproject.toml
```

Inside `src` there is a `jlt` package. Each tool has its own subfolder, plus a shared subpackage for code reused across tools:

```
src/
    jlt/
        cli.py               ---> Top-level CLI entry point (the jlt command)
        tool_1/              ---> Source code for tool 1
        tool_2/              ---> Source code for tool 2
        ...
        tool_n/              ---> Source code for tool n
        shared_knowledge/    ---> Source code shared by all tools
```

## Coding Style

When writing or modifying code in this repository, follow the conventions described in [`codying_and_style_instructions_ENG.md`](../instructions/generic_instruction/codying_and_style_instructions_ENG.md).
That file is the single source of truth for the coding style and is kept separate from this summary so it can be updated independently.
