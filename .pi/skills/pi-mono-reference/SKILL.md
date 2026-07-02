---
name: pi-mono-reference
description: Build/extend the Lena.ai chat agent. Lena uses @earendil-works/pi-agent-core as its main ReAct agent runtime (dependency), and takes DESIGN reference from the Pi Mono Agent harness for session management and context assembly. Use for ReAct loop, tools, streaming/events, session management, context assembly/compaction, steering/follow-up, backend/frontend split. Triggers: "build the chat agent", "add a tool", "stream responses", "ReAct agent", "reference pi mono", "how does pi do X", "agent loop", "session management", "context assembly", "context compaction".
---

# Pi Mono Reference (Lena.ai chat agent)

Lena = Azure cloud admin chat agent. Two relationships with Pi Mono, keep separate:

- **pi-agent-core = DEPENDENCY.** Lena's ReAct runtime. Build on it, don't reimplement.
- **Pi Mono harness = DESIGN reference.** For session management + context assembly. Read the concept, build Lena's own under `src/backend`.

Reference repo (read-only, never edit): `/Users/weixianzhang/projects/open_source/pi`

Rules:
- No model-provider assumption (no Foundry/OpenAI/Anthropic). Agent takes a `Model`; provider = config.
- Depend on pi-agent-core; don't vendor harness code.
- READMEs/source = source of truth. Read, don't guess.

## Packages

- `pi-agent-core` = Lena's ReAct engine (DEPENDENCY). `Agent`, agent loop, tools, events, steering/follow-up, `convertToLlm`/`transformContext`.
- `pi-ai` = `Model` abstraction (provider-agnostic, transitively used).
- `pi-coding-agent` = harness. DESIGN reference only (sessions, context assembly).

## Reference Map

| Building | Read in pi-mono | Type |
|---|---|---|
| ReAct runtime | `packages/agent/README.md`, `src/agent.ts`, `src/agent-loop.ts` | DEPENDENCY |
| Agent types/state | `packages/agent/src/types.ts` | `AgentMessage`, `AgentState`, `AgentTool`, events |
| Tools | `packages/agent/README.md` (Tools) | TypeBox params, `execute`, `onUpdate`, throw-on-error |
| Model selection | `packages/ai/README.md`, `src/index.ts`, `src/models.ts`, `src/types.ts` | provider from config, NOT assumed |
| Env keys | `packages/ai/src/env-api-keys.ts` | reading provider creds |
| Session management | `coding-agent/docs/sessions.md`, `docs/session-format.md`, `agent/src/harness/session/` | DESIGN ref |
| Context assembly | `agent/src/agent-loop.ts` (`transformContext`/`convertToLlm`), `coding-agent/docs/compaction.md`, `agent/src/harness/compaction/` | DESIGN ref |
| Backend→browser streaming | `agent/src/proxy.ts`, README (Proxy Usage) | `streamProxy` |
| Event flow / SSE | `packages/agent/README.md` (Event Flow) | `prompt()` + tool events |
| System prompt / templates | `agent/src/harness/system-prompt.ts`, `prompt-templates.ts`, `docs/prompt-templates.md` | |

Directory listed = `ls` first, then read the file.

## Patterns

**1. ReAct runtime (pi-agent-core, DEPENDENCY)**
- Lena's agent = `Agent` class. Give it `systemPrompt`, `Model`, `tools`.
- Prefer `Agent` over raw `agentLoop()` (`message_end` barrier before tool preflight = auditable Azure calls).
- ReAct loop (reason→act→observe→repeat) = the agent loop. Don't build your own.
- `convertToLlm` required if Lena adds custom message types (e.g. `resource_result`, `chart` not shown to LLM).

**2. Provider (pi-ai, stay agnostic)**
- `getModel(provider, modelId)` where provider/modelId come from config/env.
- Never hardcode a provider anywhere.

**3. Session management (DESIGN ref → build own)**
- Read `docs/session-format.md`, `docs/sessions.md`, `agent/src/harness/session/`.
- Carry over: append-only JSONL transcript, one record per message/event, resumable/replayable, transcript separate from live `AgentState`.
- Keep sessions replayable to feed `src/evaluation/*.yaml`.

**4. Context assembly (DESIGN ref → build own)**
```
AgentMessage[] → transformContext() → AgentMessage[] → convertToLlm() → Message[] → LLM
```
- `transformContext` = compaction/pruning/external-context injection. See `docs/compaction.md`, `harness/compaction/`.
- `convertToLlm` = filter UI-only messages, map custom types to LLM form.
- Long Azure sessions overflow context → wire compaction into `transformContext`.

**5. Tools = Azure surface**
Each Azure capability (resource graph, cost, deploy, KQL) = `AgentTool`:
- TypeBox `parameters`.
- `execute(id, params, signal, onUpdate)` throws on failure (never error strings as content).
- `onUpdate` streams long `az` commands.
- `executionMode: "sequential"` for mutations, `parallel` for read-only.
- `beforeToolCall` gates destructive ops (confirm).

**6. Backend/frontend split**
- `src/backend` hosts `Agent` + creds; `src/frontend` talks to it.
- Model on `agent/src/proxy.ts` + README Proxy Usage.
- Backend streams `AgentEvent`s (SSE/WebSocket); frontend `streamProxy`-style so creds never hit browser.
- Map events: `agent_start`→`turn_start`→`message_update` deltas→`tool_execution_*`→`agent_end`.

## Workflow

1. Pick layer from Reference Map; note DEPENDENCY vs DESIGN ref.
2. `read` the README section + source file(s) in the reference repo.
3. DEPENDENCY → use pi-agent-core API directly. DESIGN ref → summarize concept, build Lena's version in `src/backend`/`src/frontend`.
4. Custom message types, tools, session store, context logic, system prompt live in Lena. Never edit pi-mono.
5. Tools follow throw-on-error + `executionMode` rules.
6. No hardcoded provider; keep it config-driven.
