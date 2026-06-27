# Shared code across JLT tools (`shared_knowledge`)

Code that is reused by more than one JLT tool lives under
[`src/jlt/shared_knowledge/`](../../src/jlt/shared_knowledge/) instead of being duplicated
inside a single tool. This file documents what is shared, which tools use it, and the
cross-tool touchpoints — as required by the repo conventions
([`coding_convention_istructions.md`](../instructions/generic_instruction/coding_convention_istructions.md)).

Everything listed here already lives in `shared_knowledge`, so this is a description of the
existing shared surface rather than a proposal to move code there.

## `config_io.py`

Reads and writes a configuration as a plain dictionary, isolating the on-disk format. It
supports reading `toml` and `json`, and writing `json` and `toml`.

- `read_config_file(path)` — parse a `.json`/`.toml` file into a dict.
- `write_config_file(path, data)` — serialise a dict to `.json`/`.toml` (creates parent dirs).

**Used by :**

- the **backend** subsystem — to persist a backend configuration as `json` ;
- the **autoresearch registry** — to read/write each experiment's `info.json` ;
- **autoresearch config update** — to read a config file back after the LLM rewrites it, for the
  key-path comparison (see [`autoresearch_run.md`](autoresearch_run.md#safe-configuration-update)).

**Recent addition :** a TOML **writer** (`_write_toml`, registered in `WRITERS`) so config files
can be rewritten in `.toml` as well as `.json`. The Python standard library can read `toml`
(`tomllib`) but cannot write it, so this introduced the single **core** dependency `tomli-w` in
`pyproject.toml`. The import is lazy (inside `_write_toml`), matching the backend-SDK pattern, so
simply importing `config_io` never requires the package.

## `paths.py`

- `get_config_dir()` — the JLT configuration root, resolved as
  `JLT_CONFIG_DIR` → `$XDG_CONFIG_HOME/jlt` → `~/.config/jlt`.

**Used by :** every tool, to namespace its own data under `<config_dir>/<tool_name>/` (e.g. the
backend under `backend/`, autoresearch under `autoresearch/`).

## `backend/`

The unified LLM interface : a tool asks "the backend" for an answer without caring which provider
(Claude, ChatGPT, Ollama, GitHub Copilot) actually responds.

- `generic_backend` (`backend/generic.py`) — the abstract template implementing the high-level
  behaviour (`read_file`, `read_files`, `write_file`, `modify_file`, `chat`, config
  loading/saving) on top of two provider-specific primitives (`check_config`, `_chat`).
- `load_backend(name=None)` (`backend/registry.py`) — instantiate the active (or a named)
  backend, ready to use.

**Used by :** **autoresearch run**, which drives the whole optimisation round through the active
backend.

**Recent additions :**

- a public `chat(prompt, system=None)` passthrough to `_chat`, so a tool can send a free-form
  prompt (e.g. `autoresearch`'s round context) without reaching into the "private" primitive. The
  backend stays stateless — any conversation memory is the caller's responsibility.
- hardened `modify_file` : the "is the prompt a file path ?" check (`Path(prompt).is_file()`)
  raised `OSError` ("File name too long") when given a long instruction string ; it is now guarded
  so any such error simply means "treat the prompt as instructions". This benefits every caller,
  not just `autoresearch`.

## Note on what counts as "shared"

`config_io`, `paths` and `backend` are generic by design and already sit in `shared_knowledge`.
When implementing a new tool, prefer reusing these helpers over re-implementing format IO, config
path resolution or LLM access. If a tool grows code that another tool would benefit from, move it
here and add it to this file.
