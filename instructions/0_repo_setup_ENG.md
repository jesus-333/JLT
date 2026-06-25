# Repo Setup

Hi Claude.

This is a repo where I want to develop a Python package called **Jesus's LLM Tools (JLT)**.
As the name suggests, it will be a collection of tools that use LLMs.

I need your help to finish setting up the repo.

## CLI Usage

When a tool is used, it must be called from the `cli` with the following syntax:

```
jlt <tool_name> <tool_subcommand, tool_variable, tool_flags>
```

Where:
- `jlt` is the acronym for the whole project
- `<tool_name>` is the name of the specific tool
- `<tool_input>` covers all possible subcommands/inputs/flags for the specific tool

## Repository Structure

An initial structure has already been created for the repo:

```
  instructions/   ---> Folder with all the instructions
  scripts_sh/     ---> Folder for any shell scripts to be used in the future
  src/            ---> Folder for all the JLT source code
  tutorial/       ---> Old folder. Can be ignored
  LICENSE
  README.md
  pyproject.toml
```

Inside `src`, there is already a `jlt` folder. Each tool will then have its own subfolder inside it, e.g.:

```
  src/
      jlt/
          tool_1/              ---> Source code for tool 1
          tool_2/              ---> Source code for tool 2
          ...
          tool_n/              ---> Source code for tool n
          shared_knowledge/    ---> Source code shared by all tools
```

## Tools to Set Up

The repo needs to be prepared for the development of two tools: `autoresearch` and `club`.
