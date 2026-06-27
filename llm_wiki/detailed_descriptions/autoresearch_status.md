# `autoresearch` — Status & Roadmap

This document tracks, at a glance, **what is implemented and what is still pending** in the
`autoresearch` tool, plus the open design decisions worth revisiting. It is intentionally
kept short : the *how it works* detail lives in the dedicated deep-dives.

- User-facing reference (flags, examples, storage) :
  [`summaries/autoresearch.md`](../summaries/autoresearch.md).
- How experiment management works (`add`/`list`/`remove`, validation, registry) :
  [`autoresearch_config.md`](autoresearch_config.md).
- How `run` / `sync` work : [`autoresearch_run.md`](autoresearch_run.md).
- Shared-code touchpoints : [`shared_knowledge.md`](shared_knowledge.md).
- Original specifications : [`instructions/autoresearch/`](../instructions/autoresearch/).

_Last updated : 2026-06-27 — after implementing `run` (one round per invocation) and `sync`._

## The vision (where this is going)

`autoresearch` is a CLI take on Karpathy's *autoresearch* idea. The intended end-to-end
workflow (see
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

Today, steps 1–3 work for a **single round** per `run` invocation ; the looping of step 3.4
and the final report of step 4 are the main pieces still missing.

## Status at a glance

| Component | Status | Notes |
|---|---|---|
| CLI structure (all subcommands wired) | ✅ Done | `add`, `list`/`ls`, `remove`/`rm`, `run`, `sync`. |
| `add` / `list` / `remove` | ✅ Done | Register / list / unregister experiments. See [config deep-dive](autoresearch_config.md). |
| `run` | ✅ Done | Runs **one optimisation round** per invocation. See [run deep-dive](autoresearch_run.md). |
| `sync` | ✅ Done | Copies the log folder ↔ internal backup (`--reverse` to restore). |
| Round counter (`round.txt`) | ✅ Done | Created `=0` at `add` time, incremented at the end of each round. |
| Per-round logs (`round_<i>.md`) | ✅ Done | Built from an internal template; 3 sections filled by the LLM. |
| Per-round metric tracking (`csv` + `txt`) | ✅ Done | `metrics.csv` (`round,<metric_name>`) + `metrics.txt`. |
| `summary_log.md` updates | ✅ Done | Placeholder at `add` time; rewritten by the LLM each round. |
| Safe config edits (backup + key check) | ✅ Done | Recursive key-path comparison; retried up to 3× then errors. |
| LLM / backend integration | ✅ Done | Stateless backend + forwarded in-memory round context. |
| Multi-round loop / convergence / final report | ⛔ Not started | The main remaining work (see roadmap below). |

## Roadmap / open decisions

- **Multi-round loop, convergence criterion, final report — not started.** Each
  `jlt autoresearch run` currently performs exactly **one** round ; repeated runs accumulate
  `round_<i>.md` files and metric rows. Looping until a stopping criterion is met, and
  producing a final report, are the next major features.
- **Conversation memory is simulated, not multi-turn.** The backend stays stateless ; the
  runner forwards a growing in-memory transcript (`round_context`) into each call. Revisit if
  a true multi-turn backend session is ever wanted.
- **The registry format is provisional.** The on-disk schema (`info.json` fields, folder
  layout) may change as the tool evolves.
- **Duplicate experiment names raise an error** (the user must `remove` first). Could become
  an explicit update/overwrite if desired.
- **The numeric-return check is intentionally lenient** : it warns (rather than errors) on
  annotations it cannot positively classify as non-numeric. Revisit if a stricter check is
  preferred.
