---
name: openclaw-design-reference
license: MIT
metadata:
  author: weixian-zhang
  version: "1.0.0"
description: "Reference the OpenClaw open-source codebase for architecture and module-design ideas when building a custom chat agent (the lena.azure project). Use OpenClaw as an OPINION and prior art to compare against — NOT as a design to copy verbatim. ONLY use this skill when the user explicitly mentions the trigger keyword 'ref-openclaw'. Do NOT activate on general chat-agent design questions unless 'ref-openclaw' is present in the request. WHEN: ref-openclaw."
---

# Chat Agent Design Reference (via OpenClaw)

> **ACTIVATION — READ FIRST**
>
> Use this skill **only** when the user explicitly mentions the trigger keyword
> **`ref-openclaw`**. If `ref-openclaw` is not present in the request, do not load
> or apply this skill — even for general chat-agent / agent-loop design questions.

> **PURPOSE — READ FIRST**
>
> This skill helps design a **custom chat agent** (the `lena.azure` project) by
> studying the **OpenClaw** codebase as a mature, real-world reference
> implementation.
>
> **OpenClaw is a reference, not a template.**
> - Treat its choices as **one informed opinion**, not the answer.
> - **Do NOT copy** its code, structure, or file layout wholesale.
> - Extract *principles* and *tradeoffs*, then adapt to lena.azure's own goals,
>   scale, and constraints.
> - When OpenClaw's approach is over-engineered for lena.azure, say so and propose
>   a simpler alternative.

## Reference repo location

```
/Users/weixianzhang/projects/open_source/openclaw
```

Key paths worth reading when a design question comes up:

| Topic | Where to look |
|-------|---------------|
| High-level runtime architecture | `docs/agent-runtime-architecture.md`, `docs/openclaw-agent-runtime.md` |
| Concept docs (best starting point) | `docs/concepts/*.md` |
| Reusable agent core (loop, harness, types) | `packages/agent-core/src/` |
| Harness design (env, session storage, phases) | `packages/agent-core/src/harness/`, esp. `harness/types.ts`, `harness/agent-harness.ts` |
| Session storage (JSONL tree, forking) | `packages/agent-core/src/harness/session/`, `docs/concepts/session.md` |
| LLM/provider abstractions | `packages/llm-core/`, `packages/llm-runtime/`, `src/llm/` |
| Built-in agent runtime + tool wiring | `src/agents/` |
| Channels + routing (multi-channel, session keys) | `src/channels/`, `docs/channels/channel-routing.md`, `docs/concepts/multi-agent.md` |
| Gateway / transport / protocol | `docs/concepts/architecture.md`, `docs/gateway/protocol.md`, `packages/gateway-protocol/`, `src/gateway/` |
| Tools + tool policy | `src/agents/agent-tools*.ts`, `src/tools/`, `docs/tools/` |
| Plugin / extension surface | `packages/plugin-sdk/`, `docs/plugins/` |

## Highest-value concept docs to read

Prefer the docs over the source when learning a pattern — they are concise and
explain *why*. Read the specific file with the `read` tool:

- `docs/concepts/agent-loop.md` — intake → context → inference → tools → stream → persist
- `docs/concepts/agent.md` — single embedded runtime, workspace, bootstrap files
- `docs/concepts/context.md` — what the model sees, how the window is budgeted
- `docs/concepts/system-prompt.md` — how the system prompt is assembled per run
- `docs/concepts/session.md` — session routing, isolation, lifecycle, persistence (JSONL)
- `docs/concepts/streaming.md` — block streaming, chunking, partial replies
- `docs/concepts/compaction.md` — summarizing long histories to fit the window
- `docs/concepts/queue.md` + `docs/concepts/queue-steering.md` — concurrency, steering
- `docs/concepts/multi-agent.md` — routing across multiple agents/sessions
- `docs/channels/channel-routing.md` — channel abstraction, session keys, agent selection
- `docs/concepts/architecture.md` + `docs/gateway/protocol.md` — gateway/transport (WebSocket) topology and wire protocol

## How to use this skill in a design conversation

1. **Clarify lena.azure's requirement first.** Scale, channels, single vs multi
   user, hosted vs local, latency needs. Design follows requirements, not
   OpenClaw.
2. **Locate the analogous concern in OpenClaw.** Use the tables above; read the
   matching `docs/concepts/*.md`, then the source only if needed.
3. **Summarize OpenClaw's approach as an opinion** — the pattern, and the
   tradeoffs it accepts.
4. **Recommend for lena.azure explicitly.** State whether to adopt, simplify, or
   diverge, and why. Call out where OpenClaw is heavier than lena.azure needs.
5. **Never paste OpenClaw source.** Describe the idea; write fresh code that
   fits lena.azure's own module boundaries and naming.

## Distilled design principles (see references for detail)

OpenClaw's architecture, read as opinion:

- **One serialized agent loop per session.** Runs are queued per session lane to
  keep transcript + tool state consistent. → `references/architecture-notes.md`
- **Owned, rebuilt-per-run system prompt.** Prompt assembly is centralized and
  deterministic, not scattered. → `references/architecture-notes.md`
- **Clear module boundaries via a reusable core.** `agent-core` (loop, types,
  harness) is separate from the host runtime and from provider/transport code.
- **Context window is a first-class budget.** Explicit accounting of system
  prompt, history, tool schemas, attachments; compaction + pruning free space.
- **Tools behind a policy + hook pipeline.** `before_tool_call` / `after_tool_call`
  hooks and tool policy gate execution instead of ad-hoc checks.
- **Streaming is decoupled from persistence.** Deltas stream to the client while
  a separate write-locked path persists the transcript.
- **The harness abstracts the environment.** The agent loop runs against an
  `ExecutionEnv` (filesystem + shell) and a `SessionStorage` contract, so it can
  run local, sandboxed, or remote without changing the loop. → notes §9
- **Channels are a deterministic routing layer.** Inbound messages map to an
  agent + session key by explicit rules; the model never picks a channel. → §10
- **Transport/gateway is separate from agent logic.** A single WebSocket gateway
  owns all channels; the agent runtime is a distinct concern behind it. → §11

Full notes and a lena.azure-oriented "adopt / simplify / skip" table:
[`references/architecture-notes.md`](./references/architecture-notes.md)

## Guardrails

- OpenClaw is large and production-hardened for many channels and providers.
  lena.azure likely needs a **fraction** of it — resist importing its complexity.
- Cite the specific OpenClaw file you drew a pattern from so the user can verify.
- If a pattern's rationale isn't clear from the docs, read the source before
  asserting it; do not guess.
- Respect OpenClaw's license; this is for learning/reference, not copying.
