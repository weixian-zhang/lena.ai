---
name: pi-mono-reference
description: Reference the Pi mono repo open-source codebase for architecture and module-design ideas when building a custom chat agent (the lena.azure project). Use the Pi Mono harness as an OPINION and prior art to compare against — NOT as a design to copy verbatim. ONLY use this skill when the user explicitly mentions the trigger keyword 'ref-pi'. Do NOT activate on general chat-agent design questions unless 'ref-pi' is present in the request. WHEN: ref-pi.
---

# Pi Mono Reference (Lena.azure chat agent)

Lena = Azure cloud admin chat agent. This skill exists so Lena can **reference**
the Pi monorepo without **copying** its design or code.

## The one rule

> **Reference the Pi monorepo. Do not copy its design or code into Lena.**

Two distinct relationships — keep them separate:

- **`pi-agent-core` / `pi-ai` = npm DEPENDENCIES.** Call their APIs. Never vendor,
  fork, or paste their source into Lena.
- **Pi Mono harness (`pi-coding-agent`, `agent/src/harness/*`) = DESIGN reference.**
  Read the concept, then build Lena's own version under `src/backend` /
  `src/frontend`. Do not lift files.

Non-negotiables:
- No model-provider assumption (no Foundry/OpenAI/Anthropic). Agent takes a
  `Model`; provider comes from config/env.
- READMEs/source in the reference repo = source of truth. Read, don't guess.
- **Reference repo is read-only, never edit:** `/Users/weixianzhang/projects/open_source/pi`

## Architecture research notes (read these first)

Distilled, indexed notes live in [`notes/`](notes/README.md). They map into the
reference repo and capture the design concepts — but the repo is the source of
truth; confirm against live source before building.

| Note | Topic | Relationship |
|------|-------|--------------|
| [notes/01-agent-runtime.md](notes/01-agent-runtime.md) | `Agent`, agent loop, events, tools, steering | DEPENDENCY (`pi-agent-core`) |
| [notes/02-model-provider.md](notes/02-model-provider.md) | `Model`, providers, `getModel`, env keys, faux provider | DEPENDENCY (`pi-ai`), agnostic |
| [notes/03-sessions.md](notes/03-sessions.md) | JSONL tree sessions, entry types, `SessionManager` | DESIGN ref → build own |
| [notes/04-context-compaction.md](notes/04-context-compaction.md) | `transformContext`/`convertToLlm`, compaction, branch summary | DESIGN ref → wire in |
| [notes/05-harness-lifecycle.md](notes/05-harness-lifecycle.md) | `AgentHarness` phases, save points, durability | DESIGN ref (advanced) |
| [notes/06-proxy-streaming.md](notes/06-proxy-streaming.md) | backend/frontend split, `streamProxy`, SSE mapping | DESIGN ref → Lena split |

## Packages

- `pi-agent-core` = Lena's ReAct engine (DEPENDENCY). `Agent`, agent loop, tools,
  events, steering/follow-up, `convertToLlm`/`transformContext`.
- `pi-ai` = `Model` abstraction (provider-agnostic, transitively used).
- `pi-coding-agent` = harness. DESIGN reference only (sessions, context assembly).

## Reference Map (repo paths → note)

| Building | Read in pi-mono | Note / Type |
|---|---|---|
| ReAct runtime | `packages/agent/README.md`, `src/agent.ts`, `src/agent-loop.ts` | 01 · DEPENDENCY |
| Agent types/state | `packages/agent/src/types.ts` | 01 · `AgentMessage`, `AgentState`, `AgentTool`, events |
| Tools | `packages/agent/README.md` (Tools) | 01 · TypeBox params, `execute`, `onUpdate`, throw-on-error |
| Model selection | `packages/ai/README.md`, `src/index.ts`, `src/models.ts`, `src/types.ts` | 02 · provider from config, NOT assumed |
| Env keys | `packages/ai/src/env-api-keys.ts` | 02 · reading provider creds |
| Session management | `coding-agent/docs/sessions.md`, `docs/session-format.md`, `agent/src/harness/session/` | 03 · DESIGN ref |
| Context assembly | `agent/src/agent-loop.ts`, `coding-agent/docs/compaction.md`, `agent/src/harness/compaction/` | 04 · DESIGN ref |
| Harness lifecycle | `agent/docs/agent-harness.md`, `agent/docs/durable-harness.md`, `agent/src/harness/agent-harness.ts` | 05 · DESIGN ref |
| Backend→browser streaming | `agent/src/proxy.ts`, README (Proxy Usage / Event Flow) | 06 · `streamProxy` |
| System prompt / templates | `agent/src/harness/system-prompt.ts`, `prompt-templates.ts`, `coding-agent/docs/prompt-templates.md` | — |

Directory listed = `ls` first, then read the file.

## Patterns

**1. ReAct runtime (pi-agent-core, DEPENDENCY)** — see note 01
- Lena's agent = `Agent` class. Give it `systemPrompt`, `Model`, `tools`.
- Prefer `Agent` over raw `agentLoop()` (`message_end` barrier before tool preflight
  = auditable Azure calls).
- ReAct loop (reason→act→observe→repeat) = the agent loop. Don't build your own.
- `convertToLlm` required if Lena adds custom message types (e.g. `resource_result`,
  `chart` not shown to LLM).

**2. Provider (pi-ai, stay agnostic)** — see note 02
- `getModel(provider, modelId)` where provider/modelId come from config/env.
- Never hardcode a provider anywhere.

**3. Session management (DESIGN ref → build own)** — see note 03
- Carry over: append-only JSONL transcript, tree via `id`/`parentId`, resumable/
  replayable, transcript separate from live `AgentState`.
- Keep sessions replayable to feed `src/evaluation/*.yaml`.

**4. Context assembly (DESIGN ref → build own)** — see note 04
```
AgentMessage[] → transformContext() → AgentMessage[] → convertToLlm() → Message[] → LLM
```
- `transformContext` = compaction/pruning/external-context injection.
- `convertToLlm` = filter UI-only messages, map custom types to LLM form.
- Long Azure sessions overflow context → wire compaction into `transformContext`.

**5. Tools = Azure surface** — see note 01
Each Azure capability (resource graph, cost, deploy, KQL) = `AgentTool`:
- TypeBox `parameters`; `execute(id, params, signal, onUpdate)` throws on failure
  (never error strings as content); `onUpdate` streams long `az` commands.
- `executionMode: "sequential"` for mutations, `parallel` for read-only.
- `beforeToolCall` gates destructive ops (confirm).

**6. Backend/frontend split** — see note 06
- `src/backend` hosts `Agent` + creds; `src/frontend` talks to it.
- Backend streams `AgentEvent`s (SSE/WebSocket); creds never hit browser. Use
  `streamProxy`-style transport only if the loop must run client-side.
- Map events: `agent_start`→`turn_start`→`message_update` deltas→`tool_execution_*`→`agent_end`.

## Workflow

1. Pick the layer from the Reference Map; note DEPENDENCY vs DESIGN ref.
2. Open the matching `notes/` file for the file map + concept.
3. `read` the cited README section + source file(s) in the reference repo (source
   of truth). Never edit pi-mono.
4. DEPENDENCY → use the pi-agent-core / pi-ai API directly. DESIGN ref → summarize
   the concept, then build Lena's own version in `src/backend` / `src/frontend`.
5. Custom message types, tools, session store, context logic, system prompt live
   in Lena — reference pi's design, don't copy its code.
6. Tools follow throw-on-error + `executionMode` rules. No hardcoded provider.
