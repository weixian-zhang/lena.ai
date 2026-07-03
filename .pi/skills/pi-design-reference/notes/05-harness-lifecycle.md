# Note 5 — AgentHarness lifecycle (DESIGN reference, advanced)

The orchestration layer pi is building **above** the low-level loop: session
persistence, runtime config, save points, phases, durability. **Reference for
when Lena's backend outgrows a bare `Agent`.** Design notes, partly in-progress
in the repo — treat as direction, not a stable API. Do not copy.

Reference (read-only):
- `packages/agent/docs/agent-harness.md` — lifecycle, phases, save points, state model
- `packages/agent/docs/durable-harness.md` — semi-durable recovery design
- `packages/agent/docs/hooks.md` — target hook system
- `packages/agent/docs/observability.md`
- `packages/agent/src/harness/agent-harness.ts` — reference implementation

## Why it exists

`Agent` runs one conversation well. `AgentHarness` adds: owning the session,
letting config change mid-run without corrupting an in-flight provider request,
queuing writes safely, and (eventually) crash recovery.

## Four-part state model (the useful idea)

1. **Harness config** — latest runtime config (model, thinking level, tools,
   active tools, resources, stream options, system prompt). Getters return this,
   NOT the in-flight snapshot. Setters take effect on the *next* turn.
2. **Turn snapshot** — concrete state for one LLM turn, built by
   `createTurnState()`. All logic for that turn uses the same snapshot; the
   in-flight provider request is never mutated.
3. **Session** — persisted entries only. Reads don't include queued writes.
4. **Pending session writes** — writes requested while busy; queued and flushed
   deterministically at save points / settlement / failure cleanup.

## Phases

```
type AgentHarnessPhase = "idle" | "turn" | "compaction" | "branch_summary" | "retry";
```

- Structural ops (`prompt`, `skill`, `promptFromTemplate`, `compact`,
  `navigateTree`) require `idle` and set phase before the first `await`; starting
  another while busy rejects with `"busy"`.
- Allowed during a turn: `steer`, `followUp`, `nextTurn`, `abort`, config setters.

## Save points (the key mechanism)

A save point = after an assistant turn + its tool results complete. There the
harness (1) flushes pending writes after that turn's messages, (2) builds a fresh
turn snapshot if the loop may continue, (3) applies new context/model/thinking/
stream-options/session-id before the next provider request. This is how mid-run
config changes take effect **without touching the running request**.

`AssistantMessageStream` decouples provider transport (SSE/websocket reads) from
downstream consumption, so the harness can `await` listeners/hooks/persistence
without stalling the transport or reordering the transcript.

## Error model

- Low-level capabilities return `Result<TValue, TError>` (non-throwing:
  `ExecutionEnv`, fs/shell, resource loading, compaction helpers).
- High-level mutation APIs (`Session`, `AgentHarness`) reject/throw; public
  failures normalize to `AgentHarnessError` with `cause`.

## Durability direction (durable-harness.md)

A **fully** durable harness isn't realistic — tools, models, auth, extensions,
resource loaders, system-prompt callbacks are runtime JS the host must recreate.
Target = **semi-durable**: the session is the durable append-only state tree;
the harness persists only serializable state it owns (active tool names, queued
steer/followUp/nextTurn, pending writes, operation/turn markers). On resume the
app re-registers runtime deps; recovery restarts from durable boundaries.
Provider streams are not resumable. Non-idempotent tool calls are not auto-retried.

## Lena mapping

- Start Lena's backend with a plain `Agent` (note 1). Only reach for harness-style
  structure when you need mid-run config changes, safe concurrent writes, or
  crash recovery.
- If Lena needs recovery, adopt the **semi-durable** stance: session = durable
  truth; re-register Azure tools/creds on resume; never auto-retry mutating Azure
  tool calls (they have real side effects) unless explicitly marked idempotent.
- Build Lena's own harness/orchestrator; use this doc as the blueprint only.
