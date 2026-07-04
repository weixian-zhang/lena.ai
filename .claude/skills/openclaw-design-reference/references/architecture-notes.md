# OpenClaw Architecture Notes (Reference / Opinion)

These notes distill how OpenClaw structures a chat-agent runtime. Use them as
**prior art to reason against** while designing lena.azure — not as a blueprint to
copy. Every section ends with a lena.azure-oriented take.

Source of truth: `/Users/weixianzhang/projects/open_source/openclaw`
(read `docs/concepts/*.md` and `packages/agent-core/src/` for specifics).

---

## 1. Module boundaries

OpenClaw separates concerns into distinct layers:

- `packages/agent-core/` — reusable agent loop, message/tool types, harness,
  compaction, session storage contracts. Host-agnostic.
- `packages/llm-core/` + `src/llm/` — model/provider registry, transport,
  provider-specific stream adapters. The loop depends on a `StreamFn` contract,
  not on any specific provider.
- `src/agents/` — the concrete host runtime that wires tools, prompts, sessions,
  channels, and provider auth together.
- `src/gateway/` + `packages/gateway-protocol/` — WebSocket transport and the
  typed wire protocol; owns channels/messaging, separate from agent logic.
- `packages/plugin-sdk/` — the only surface plugins are allowed to import;
  internals under `src/**` are off-limits to extensions.

**Principle:** the *core loop* knows nothing about providers, transports, or UI.
It depends on narrow contracts (a stream function, tool interfaces, a session
store).

**lena.azure take:** adopt the core/provider/transport split even at small scale —
it keeps the loop testable. You likely do NOT need a plugin SDK, a multi-package
monorepo, or a gateway-protocol codegen layer on day one. Start with a single
package that internally keeps these as folders/modules with clean interfaces.

---

## 2. The agent loop

Pipeline (from `docs/concepts/agent-loop.md`):

```
intake → context assembly → model inference → tool execution → streaming replies → persistence
```

Key properties:

- **One serialized run per session.** Runs are queued on a per-session lane (and
  optionally a global lane) to prevent tool/session races.
- **Events, not return values.** The loop emits lifecycle (`start/end/error`),
  `assistant` deltas, and `tool` events on streams; callers subscribe.
- **The stream contract never throws for model/runtime failures.** Failures are
  encoded as events + a final message with `stopReason: "error" | "aborted"`.
  (See `packages/agent-core/src/types.ts` `StreamFn` doc.)
- **Tool execution modes:** `sequential` vs `parallel` per assistant message.

**lena.azure take:** the event-stream + per-session serialization model is worth
copying conceptually. The failure-as-events contract is a genuinely good idea —
it avoids half-streamed error states. Parallel tool execution can wait until you
have a real need.

---

## 3. Context = everything sent to the model

From `docs/concepts/context.md`:

- Context is bounded by the model's window and is explicitly budgeted:
  system prompt + conversation history + tool calls/results + attachments +
  compaction artifacts + hidden provider wrappers.
- OpenClaw can *report* per-contributor sizes (`/context list|detail|map`).
- **Tools cost twice:** the tool-list text AND the JSON tool schemas both count.
- Skills are listed as metadata only; full instructions are read on demand — a
  deliberate trick to keep the window lean.

**lena.azure take:** build context accounting in from the start, even if you don't
expose a `/context` UI. Knowing where tokens go is the difference between a cheap
agent and a runaway one. The "list capability, load details on demand" pattern
is a strong default for tools/skills/docs.

---

## 4. System prompt assembly

From `docs/concepts/system-prompt.md` + `docs/concepts/agent.md`:

- The system prompt is **owned and rebuilt every run** from: base prompt + tool
  list + skills list + runtime metadata (time/host/model) + injected workspace
  bootstrap files (`AGENTS.md`, `SOUL.md`, `USER.md`, etc.) under a
  "Project Context" section.
- Large injected files are truncated per-file and capped in total.

**lena.azure take:** centralize prompt assembly in ONE function/module that is pure
and deterministic given session state. Do not let prompt fragments leak across
the codebase. The bootstrap-files idea (user-editable persona/memory files) is a
nice UX pattern if lena.azure wants a customizable persona.

---

## 5. Sessions & persistence

From `docs/concepts/session.md` + `docs/concepts/agent-loop.md` +
`packages/agent-core/src/harness/session/`:

- Transcripts stored as **JSONL**, one file per session, stable session IDs.
- **The transcript is an append-only tree, not a flat list.** Each entry has
  `id`, `parentId`, `timestamp`, and a `type` (message, thinking-level change,
  compaction marker, etc.). A "leaf" pointer marks the active branch; the prompt
  is the path from leaf to root (`getPathToRoot`). This makes **forking/branching**
  and compaction natural: compaction appends a summary entry and moves the leaf.
  (See `SessionStorage` / `SessionRepo` in `harness/types.ts`.)
- Storage is behind a `SessionStorage` interface with swappable backends:
  `jsonl-storage` (disk) and `memory-storage` (tests) implement the same API.
- Writes are guarded by a **process-aware, file-based write lock** (non-reentrant
  by default) so compaction/truncation can't race the live writer.
- Streaming to the client is decoupled from transcript persistence.

**Session routing & lifecycle** (from `docs/concepts/session.md`):

- A **session key** buckets context and controls concurrency. DMs collapse to a
  `main` session by default; groups/rooms/threads are isolated by key shape.
- `session.dmScope` controls DM isolation: `main` → `per-peer` →
  `per-channel-peer` (recommended for multi-user) → `per-account-channel-peer`.
- Sessions expire by **daily reset** (default 4AM), optional **idle reset**, or
  manual `/new` · `/reset`. Freshness tracks real user turns, not system writes.

**lena.azure take:** JSONL append-only transcripts are simple and debuggable — a
good default. The **tree/leaf model is worth adopting even if you never expose
forking**, because it makes compaction and "edit-and-retry" clean instead of
mutating a flat array. Put storage behind an interface (disk + in-memory) from
day one for testability. A write lock matters once you have concurrent writers;
if lena.azure is single-process you can start with an in-process queue and add file
locking only if needed. Pick your `dmScope` default deliberately if more than
one user can talk to lena.azure.

---

## 6. Compaction & pruning

From `docs/concepts/compaction.md` + `docs/concepts/context.md`:

- **Compaction** summarizes older history into a compact entry, persisted in the
  transcript, keeping recent messages intact. Can trigger a retry of the run.
- **Pruning** drops old tool results from the *in-memory* prompt only; the disk
  transcript stays complete.
- Compaction can be delegated to a pluggable "context engine".

**lena.azure take:** distinguish "what persists" (transcript) from "what's in the
window" (prompt). Start with simple threshold-based compaction; the pluggable
context-engine abstraction is premature unless you need swappable strategies.

---

## 7. Streaming & steering

From `docs/concepts/streaming.md` + `docs/concepts/queue-steering.md`:

- Assistant deltas stream continuously; **block streaming** can flush completed
  blocks on `text_end` or `message_end`, with soft chunking (paragraph → newline
  → sentence) and idle-based coalescing.
- **Steering:** messages arriving mid-run are injected after the current
  assistant turn's tool calls finish, before the next model call. Alternatives:
  followup / collect / interrupt.

**lena.azure take:** block streaming + chunking is a UX refinement — get raw delta
streaming working first. Steering is powerful but complex; only build it if
lena.azure users will realistically interrupt in-flight runs.

---

## 8. Tools, policy & hooks

From `docs/concepts/agent-loop.md` (hook points) + `src/agents/agent-tools*.ts`:

- Tools run through a **policy pipeline** and **before/after hooks**
  (`before_tool_call` can block; `after_tool_call` can rewrite results).
- Hooks also exist for prompt build, model resolve, compaction, session and
  message lifecycle — a consistent extension mechanism.
- `before_tool_call: { block: true }` is terminal; `{ block: false }` is a no-op
  (can't un-block) — a clean, predictable decision rule.

**lena.azure take:** a small, explicit tool-policy + hook seam is worth having early
— it centralizes safety/approval logic. You don't need the full breadth of
OpenClaw's hook catalog; start with `before_tool_call` (gate) and `after_tool_call`
(observe/transform).

---

## 9. Harness design (the loop's environment contract)

From `packages/agent-core/src/harness/` (esp. `types.ts`, `agent-harness.ts`):

The **harness** is the seam between the pure agent loop and the messy outside
world. Instead of the loop calling `fs`/`child_process`/a specific store
directly, it receives capability interfaces:

- **`ExecutionEnv` = `FileSystem` + `Shell`.** Every file/exec operation goes
  through this. Critically, **its methods never throw** — they return
  `Result<T, Error>` (`{ ok: true, value } | { ok: false, error }`). This makes
  failure handling explicit and lets you swap local, sandboxed (Docker), or
  remote environments without touching the loop.
- **`SessionStorage` / `SessionRepo`** — the append-only tree API from §5
  (create / open / fork / list / delete; append entry, get path-to-root).
- **`AgentHarnessResources`** — skills + prompt templates the app loads and can
  hot-swap via `setResources()`; the harness owns none of the loading.
- **`AgentHarnessStreamOptions`** — curated provider request options (transport,
  timeouts, retries, headers, cache hints) **snapshotted at turn start** so a
  mid-run config change can't half-apply.
- **`systemPrompt`** can be a string or a callback given `{ env, session, model,
  thinkingLevel, activeTools, resources }` — prompt assembly is injected, not
  hardcoded.
- **Phases** are explicit: `"idle" | "turn" | "compaction" | "branch_summary" |
  "retry"`. State transitions are named, not implicit.
- `getApiKeyAndHeaders(model)` injects auth lazily per model, keeping secrets out
  of the loop.

**lena.azure take:** this is the single most transferable idea for keeping a chat
agent testable. Define **narrow capability interfaces** (`ExecutionEnv`,
`SessionStorage`, a resources provider) and pass them in. The `Result`-instead-of-throw
convention for env ops is worth adopting — it kills an entire class of unhandled
exceptions mid-stream. Snapshotting per-turn options and naming phases are cheap
discipline that pay off when debugging. You do not need the full generic type
parameterization OpenClaw uses; concrete interfaces are fine.

---

## 10. Channel design & routing

From `docs/channels/channel-routing.md` + `src/channels/` +
`docs/concepts/multi-agent.md`:

- A **channel** (telegram, slack, whatsapp, webchat, plugin channels…) is an
  inbound/outbound messaging surface. **Routing is deterministic** — the model
  never chooses a channel; replies go back where the message came from.
- Inbound resolves to exactly **one agent** via an ordered match ladder:
  exact peer → parent/thread → guild+roles → guild → team → account → channel →
  default. The matched agent picks the workspace + session store.
- A **session key** encodes channel/account/peer/thread, e.g.
  `agent:main:telegram:group:-100...:topic:42`. Key shape controls isolation and
  concurrency (DMs collapse to `main`; groups/threads stay isolated).
- Cross-cutting channel concerns are isolated as their own modules: allowlists,
  mention/activation gating, typing indicators, ack reactions, inbound debounce,
  draft/progress streaming, thread bindings.
- **Broadcast groups** can fan one inbound message to multiple agents.

**lena.azure take:** even if lena.azure starts with a single web chat channel, model
the **channel as an interface** (receive → normalized inbound event; send →
normalized outbound) and keep routing deterministic and outside the model. The
**session-key-as-routing-bucket** idea is the clean way to get isolation and
concurrency control for free. Skip mention gating, broadcast, thread bindings,
and multi-account logic until a real second channel forces them.

---

## 11. Transport / gateway

From `docs/concepts/architecture.md` + `docs/gateway/protocol.md`:

- A single long-lived **WebSocket gateway** owns all messaging channels and
  control-plane clients (CLI, UI, nodes); the agent runtime is a separate
  concern behind it. One gateway per host.
- **Typed wire protocol:** first frame must be `connect`; then
  requests `{type:"req", id, method, params}` → `{type:"res", id, ok, payload|error}`
  and server-push `{type:"event", event, payload, seq?}`. Frames are validated
  against JSON Schema generated from TypeBox schemas (Swift models generated too).
- **Idempotency keys** are required for side-effecting methods (`send`, `agent`)
  so retries are safe; a short-lived dedupe cache backs this.
- Auth + device pairing live at the transport edge (shared secret / trusted
  proxy / tailnet), not in the agent.
- Events are **not replayed**; clients refresh on gaps. Runs are acknowledged
  immediately (`{runId, status:"accepted"}`) then streamed.

**lena.azure take:** only build a gateway if lena.azure serves multiple
channels/clients. For a single web UI, a plain HTTP + SSE (or one WebSocket
endpoint) is enough. But keep the *principles*: **transport separate from agent
logic**, **ack-then-stream** for long runs, **idempotency keys** on
side-effecting calls, and **schema-validated frames** if you have typed clients.
Protocol codegen (TypeBox → JSON Schema → Swift) is only worth it with multiple
native clients.

---

## Adopt / Simplify / Skip — quick table for lena.azure

| OpenClaw pattern | Recommendation for lena.azure |
|------------------|----------------------------|
| Core/provider/transport module split | **Adopt** (as folders, not packages) |
| Event-stream loop, failure-as-events | **Adopt** |
| Per-session serialized runs | **Adopt** (in-process queue first) |
| Explicit context/token budgeting | **Adopt** |
| Centralized, per-run system prompt | **Adopt** |
| JSONL transcripts | **Adopt** |
| Append-only session tree + leaf pointer | **Adopt** (clean compaction/retry) |
| Harness capability interfaces (`ExecutionEnv`, storage) | **Adopt** |
| `Result`-instead-of-throw for env ops | **Adopt** |
| Per-turn snapshot of stream/provider options | **Adopt** |
| Deterministic channel routing + session keys | **Adopt (as interface)** |
| before/after tool hooks + policy | **Adopt (minimal subset)** |
| Compaction | **Simplify** (threshold-based) |
| Block streaming + chunking | **Simplify** (raw deltas first) |
| File-based write lock | **Simplify/Defer** (until multi-writer) |
| Session forking/branching UI | **Defer** (keep the tree, skip the UI) |
| Steering (steer/followup/collect/interrupt) | **Defer** |
| Ack-then-stream + idempotency keys | **Adopt if long runs / retries** |
| Pluggable context engine | **Skip** initially |
| Plugin SDK / extension boundary | **Skip** initially |
| WebSocket gateway + protocol codegen | **Skip** unless multi-channel/native clients |
| Mention gating, broadcast, thread bindings | **Skip** until 2nd channel |
| Multi-agent routing, subagents | **Skip** unless needed |
| Monorepo of ~20 packages | **Skip** — one package with clean modules |

---

## Reminder

When you pull an idea from here into lena.azure, **write original code** that fits
lena.azure's own naming and boundaries, and **cite the OpenClaw file** you learned
it from so the reasoning is traceable. OpenClaw is the opinion; lena.azure's
requirements are the decision-maker.
