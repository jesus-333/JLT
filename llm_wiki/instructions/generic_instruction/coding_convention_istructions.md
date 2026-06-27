## Coding conventions & defaults

Beyond the style guide, the codebase follows the conventions below. 
They are defaults, not laws — if you want one changed, tell me rather than letting me guess differently each time.

- **CLI entry points** return an `int` exit code, wrap the work in `try/except`, print `Error while <action> : <error>` and return `1` on failure, and print a success line and return `0` otherwise. 
    See `backend/cli.py` and `autoresearch/cli.py`.
- **Prefer erroring over silent destructive actions.** E.g. `autoresearch add` refuses to overwrite an existing registry entry — the user must `remove` first. 
    (Contrast with `backend config`, which is intentionally a create-or-update.)
- **Store absolute, resolved paths internally**, not the path as typed by the user (so the tool keeps working regardless of the current directory later).
- **When a static check cannot be certain, warn and proceed** rather than hard-failing valid code; only raise an error for cases you can positively classify as wrong.
    Example: the numeric-return check in`autoresearch/manage/validation.py` accepts recognized numeric annotations, errors on recognized non-numeric ones (`str`, `list`, …), and merely *warns* on annotations it cannot classify (`float | None`, generics, missing).
- **Registry / metadata files** are JSON written sorted (via the shared `config_io`). Their on-disk schema is provisional and may change as the tools evolve.
- As a rule of thumb when you have to implement functions that have to check some input parameters et similia if something is detacted that is wrong always throw an error.
    E.g. If you have to write a function that must receive in input a positive number, when you write the check for that input, throw an exception if receive any input that is not a positive number.
    Do not fall back to some default value. Basically better safe than sorry.
    There can be of exception to this rule but you have to motivate them very carefully.
- If you have any doubt during implementation follow the "occam's razor"... or put it directly "simpler is better". 
    Write the code as clear as possible. 
    Try to avoid function too long or complex. 
    If you noticed that similar code is used in more sections create a function with that code.
    Comments everything. The code MUST BE easy to read and expand in future.

## Shared code & per-tool data layout

- Code reused across tools lives under `src/jlt/shared_knowledge/`. If you implement a new tool that use code of another tool notify the user at the end of the implementation.
    Furthermore prepare also a small file where you describe which code is shared among more tools what it does, and why it might be convenient to move it into `shared_knowledge`
- The JLT config directory is shared by all tools and resolved via `JLT_CONFIG_DIR` → `XDG_CONFIG_HOME/jlt` → `~/.config/jlt`. 
    **Each tool namespaces its own data under `<config_dir>/<tool_name>/`** (e.g.`autoresearch/`). 
