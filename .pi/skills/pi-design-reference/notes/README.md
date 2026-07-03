# Pi Mono — Architecture Research Notes (index)

Quick-reference notes distilled from **reading** the Pi monorepo. These are a
map into the reference repo, not a design to copy. Always confirm against the
live source before building — the repo is the source of truth, these notes go
stale.

**Reference repo (read-only, never edit):** `/Users/weixianzhang/projects/open_source/pi`

## The one rule

> **Reference the Pi monorepo. Do not copy its design or code into Lena.**

- `pi-agent-core` and `pi-ai` are **npm dependencies** — call their APIs, never
  vendor/fork their source.
- The `pi-coding-agent` harness and the `agent/src/harness/*` internals are
  **design reference only** — read the concept, then build Lena's own version
  under `src/backend` / `src/frontend`. Do not lift files.
- No provider assumptions. Lena takes a `Model`; provider comes from config/env.

## Notes

| # | Note | Covers | Lena relationship |
|---|------|--------|-------------------|
| 1 | [01-agent-runtime.md](01-agent-runtime.md) | `Agent`, agent loop, events, tools, steering/follow-up, message flow | **DEPENDENCY** (`pi-agent-core`) |
| 2 | [02-model-provider.md](02-model-provider.md) | `Model` abstraction, providers, `getModel`, env keys, faux provider | **DEPENDENCY** (`pi-ai`), stay provider-agnostic |
| 3 | [03-sessions.md](03-sessions.md) | JSONL tree session format, entry types, `SessionManager` API | **DESIGN ref** → build own store |
| 4 | [04-context-compaction.md](04-context-compaction.md) | `transformContext`/`convertToLlm`, compaction, branch summaries | **DESIGN ref** → wire into runtime |
| 5 | [05-harness-lifecycle.md](05-harness-lifecycle.md) | `AgentHarness` phases, turn snapshots, save points, durability | **DESIGN ref** (advanced) |
| 6 | [06-proxy-streaming.md](06-proxy-streaming.md) | backend/frontend split, `streamProxy`, SSE event mapping | **DESIGN ref** → Lena backend/frontend |

## How to use these notes

1. Start from [SKILL.md](../SKILL.md) → pick the layer you're building.
2. Open the matching note for the file map + concept summary.
3. `read` the cited README section / source file in the reference repo.
4. DEPENDENCY → use the API directly. DESIGN ref → summarize, then build Lena's own.
5. Never edit anything under `/Users/weixianzhang/projects/open_source/pi`.
