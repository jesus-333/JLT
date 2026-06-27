# Backend Subsystem Summary

The **backend** subsystem gives every JLT tool a single, unified way to talk to
a Large Language Model, regardless of which provider actually answers. It is
primarily meant to be used from the command line (`jlt backend ...`), 

## Index

- [Purpose](#purpose)
- [Key ideas](#key-ideas)
- [Installation](#installation)
- [Configuration files](#configuration-files)
  - [Per-backend keys](#per-backend-keys)
  - [Where configs are stored](#where-configs-are-stored)
- [CLI reference](#cli-reference)
- [CLI examples](#cli-examples)
- [Python implementation](#python-implementation)
  - [Repository layout](#repository-layout)
  - [The `generic_backend` class](#the-generic_backend-class)
  - [Using the backend from Python](#using-the-backend-from-python)
  - [Adding a new backend](#adding-a-new-backend)

## Purpose

A tool never needs to know whether a request is served by Claude, ChatGPT, Ollama or GitHub Copilot — it just asks "the backend". The backend is exposed on the command line as a subcommand of `jlt`:

```
jlt backend <subcommand> <flags>
```

## Key ideas

- A **backend** is one configured connection to a provider (model + credentials + options).
- Each backend is saved under a **name** you choose. You can have **several backends for the same provider** — e.g. two Claude accounts save as `work_claude` and `personal_claude`.
- One backend at a time can be **active**. Tools use the active backend unless told otherwise.

## Installation

The core package has no dependency. Each backend pulls its own provider SDK
through an optional extra, so you install only what you need:

```bash
pip install jlt[claude]          # Anthropic SDK only
pip install jlt[chat_gpt]        # OpenAI SDK only
pip install jlt[github_copilot]  # GitHub Copilot SDK
pip install jlt[ollama]          # Ollama SDK only
pip install jlt[all-backends]    # every provider SDK at once
```

## Configuration files

A configuration is a plain dictionary, stored on disk as `toml` or `json`. You pass one to `jlt backend config` to create or update a backend.

**Every config must contain a `backend_type` key** — this is how the tool knows which provider to use. Supported values:

| `backend_type` | Provider |
| --- | --- |
| `claude` | Anthropic models |
| `chat_gpt` | OpenAI models |
| `ollama` | Ollama (local or cloud) |
| `github_copilot` | GitHub Copilot |

### Per-backend keys

**`claude`**

| Key | Required | Notes |
| --- | --- | --- |
| `backend_type` | yes | Must be `"claude"`. |
| `api_key` | no | Falls back to the `ANTHROPIC_API_KEY` environment variable. |
| `model` | no | Defaults to `claude-opus-4-8`. |
| `max_tokens` | no | Defaults to `16000`. |

**`chat_gpt`**

| Key | Required | Notes |
| --- | --- | --- |
| `backend_type` | yes | Must be `"chat_gpt"`. |
| `api_key` | no | Falls back to the `OPENAI_API_KEY` environment variable. |
| `model` | no | Defaults to `gpt-4o`. |
| `base_url` | no | Custom endpoint (OpenAI-compatible). |

**`ollama`**

| Key | Required | Notes |
| --- | --- | --- |
| `backend_type` | yes | Must be `"ollama"`. |
| `model` | yes | E.g. `"llama3.1"`. |
| `mode` | no | `"local"` (default) or `"cloud"`. |
| `host` | no | Defaults to `http://localhost:11434` (local) or `https://ollama.com` (cloud). |
| `api_key` | only in cloud mode | Sent as a bearer token. |

**`github_copilot`**

Runs on the official [`github-copilot-sdk`](https://github.com/github/copilot-sdk),
which handles the GitHub → Copilot token exchange (and refresh) internally. The
SDK drives a separate runtime binary, downloaded once with
`python -m copilot download-runtime` (or fetched automatically on first use).

| Key | Required | Notes |
| --- | --- | --- |
| `backend_type` | yes | Must be `"github_copilot"`. |
| `api_key` | no | An ordinary GitHub token (e.g. `gh auth token`). The alias `github_token` is also accepted. If omitted, the SDK uses the logged-in GitHub user. |
| `model` | no | Defaults to `gpt-4o`. |
| `timeout` | no | Seconds to wait for a single answer. Defaults to `300`. |

### Where configs are stored

When you run `jlt backend config`, the validated configuration is saved (always
as `json`) under the backend's own namespace (`backend/`) inside the JLT config
directory — like every other JLT tool, the backend keeps its data namespaced:

```
<config_dir>/
    backend/
        active.json                 ---> name of the active backend
        backends/
            <backend_name>.json     ---> one file per configured backend
```

`<config_dir>` is resolved in this order:

1. `$JLT_CONFIG_DIR` if set,
2. `$XDG_CONFIG_HOME/jlt` if set,
3. `~/.config/jlt` otherwise.

## CLI reference

```
jlt backend config   --backend_name <name> --path_file <path>   # create / update
jlt backend list                                                # list (alias: ls)
jlt backend activate --backend_name <name>                      # set the active backend
jlt backend remove   --backend_name <name>                      # delete (alias: rm)
```

- `config` infers the provider from the `backend_type` in `--path_file`.
- `activate` and `remove` error out if the backend is not already configured.
- Removing the active backend also clears the active pointer.

## CLI examples

### 1. Configure a Claude backend (toml)

`claude_work.toml`:

```toml
backend_type = "claude"
api_key      = "sk-ant-xxxxxxxx"
model        = "claude-opus-4-8"
```

```bash
jlt backend config --backend_name work_claude --path_file claude_work.toml
```

### 2. Configure a local Ollama backend (json)

`ollama_local.json`:

```json
{
    "backend_type": "ollama",
    "model": "llama3.1",
    "mode": "local"
}
```

```bash
jlt backend config --backend_name local_ollama --path_file ollama_local.json
```

### 3. Two accounts for the same provider

```toml
# personal_claude.toml
backend_type = "claude"
api_key      = "sk-ant-personal"
```

```bash
jlt backend config --backend_name work_claude     --path_file claude_work.toml
jlt backend config --backend_name personal_claude --path_file personal_claude.toml
```

### 4. List, activate, remove

```bash
$ jlt backend ls
Configured backends :
  - local_ollama
  - personal_claude
  - work_claude

$ jlt backend activate --backend_name work_claude
Backend 'work_claude' is now active.

$ jlt backend list
Configured backends :
  - local_ollama
  - personal_claude
  - work_claude <- active

$ jlt backend rm --backend_name personal_claude
Backend 'personal_claude' removed successfully.
```

---

## Python implementation

This section is for anyone interested in how the backend works under the hood,
or who wants to call it directly from Python (e.g. when building a new tool).

### Repository layout

The backend code lives under `src/jlt/shared_knowledge/backend/` because it is
meant to be reused by all tools.

```
src/jlt/shared_knowledge/backend/
    __init__.py          ---> re-exports the most useful entry points
    generic.py           ---> abstract template (generic_backend)
    claude.py            ---> Anthropic (Claude) backend
    chat_gpt.py          ---> OpenAI (ChatGPT) backend
    ollama.py            ---> Ollama backend (local and cloud)
    github_copilot.py    ---> GitHub Copilot backend
    registry.py          ---> stores/lists/activates/removes named backends
    cli.py               ---> the `jlt backend` command
```

Two generic helpers used by the backend are **not** backend-specific and live
one level up, directly under `src/jlt/shared_knowledge/` (so other tools can
reuse them without importing the backend package):

```
src/jlt/shared_knowledge/
    config_io.py         ---> read toml/json, write json/toml
    paths.py             ---> get_config_dir (the JLT config root)
```

### The `generic_backend` class

`generic.py` defines the abstract template every backend inherits from. It
already implements all the high-level behaviour on top of two small,
provider-specific primitives that each concrete backend must provide.

#### Methods exposed to the tools

| Method | What it does |
| --- | --- |
| `__init__(config_path)` | Receives the path to the config file. If the file exists it is read and validated immediately. |
| `update_config(config)` | Validates a config dictionary (via `check_config`) and saves it. Also called from `__init__`. |
| `update_config_from_file(file_path)` | Reads a dictionary from a `toml`/`json` file, then calls `update_config`. |
| `check_config(config)` | **Abstract.** Backend-specific validity check. Called by `update_config` before saving. |
| `chat(prompt, system=None)` | Send a single prompt to the LLM and return its answer. A thin public passthrough to the `_chat` primitive, for tools that need a free-form prompt (e.g. an interactive, multi-step exchange). The backend stays stateless — any conversation memory is the caller's responsibility. |
| `modify_file(prompt, file_to_edit, other_files=None)` | Rewrites `file_to_edit` following `prompt`. `prompt` can be the instructions themselves *or* a path to a text file containing them. `other_files` is reserved for future use. |
| `read_file(file_to_read, summarize=False)` | Reads a text file. If `summarize=True`, returns an LLM-generated summary instead. |
| `read_files(list_of_files, summarize=False)` | Same as `read_file` but for a list; results are concatenated into one string, each block prefixed with its file path. |
| `write_file(text, file_path, extension="txt")` | Creates a new text file containing `text`. The suffix of `file_path` is forced to `extension` (`txt` or `md` for now; a leading dot/uppercase is tolerated) and missing parent directories are created. Plain file write, no LLM involved. Returns the written `Path`. |

#### Provider-specific primitives

Each concrete backend implements just two methods:

- `check_config(config)` — raise an error if the config is invalid.
- `_chat(prompt, system=None)` — send one prompt to the model and return the
  text answer. All the file logic above is built on this single call.

This is what keeps adding a new provider simple.

### Using the backend from Python

```python
from jlt.shared_knowledge.backend import load_backend

# Load whichever backend is currently active...
backend = load_backend()
# ...or a specific one by name:
# backend = load_backend("work_claude")

# Read a file
text = backend.read_file("notes.md")

# Summarize a file with the LLM
summary = backend.read_file("paper.txt", summarize = True)

# Read several files into one string
combined = backend.read_files(["a.py", "b.py"])

# Write a brand new text file (no LLM involved)
backend.write_file("some content", "notes")                 # -> notes.txt
backend.write_file("# Title", "report", extension = "md")    # -> report.md

# Edit a file: instructions given directly...
backend.modify_file("Add type hints to every function", "module.py")

# ...or instructions read from a file
backend.modify_file("instructions.txt", "module.py")
```

### Adding a new backend

1. Create a new module under `backend/` (e.g. `gemini.py`).
2. Subclass `generic_backend` and implement `check_config` and `_chat`.
3. Register it in the `BACKEND_CLASSES` mapping in `registry.py` (one line).
4. (Optional) Add an optional-dependency extra in `pyproject.toml`.
