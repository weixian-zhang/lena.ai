# Note 1 — Agent runtime (`pi-agent-core`, DEPENDENCY)

Lena's ReAct engine. **Depend on it, don't reimplement or vendor.**

Reference files (read-only):
- `packages/agent/README.md` — full API surface. Read the whole thing.
- `packages/agent/src/agent.ts` — `Agent` class (~557 lines)
- `packages/agent/src/agent-loop.ts` — low-level `agentLoop` / `agentLoopContinue` (~742 lines)
- `packages/agent/src/types.ts` — `AgentMessage`, `AgentState`, `AgentTool`, `AgentEvent`, `AgentLoopConfig`
- `packages/agent/src/index.ts` — export list (what you can import)

## Mental model

`Agent` = stateful wrapper over the ReAct loop (reason → act → observe → repeat).
Give it `systemPrompt`, `model`, `tools`; call `prompt()`; subscribe to events.

```ts
const agent = new Agent({
  initialState: { systemPrompt, model, tools },
  convertToLlm,      // required if you add custom message types
  transformContext,  // optional: prune/compact/inject before each LLM call
});
agent.subscribe((event) => { /* UI updates */ });
await agent.prompt("...");
```

**Prefer `Agent` over raw `agentLoop()`.** With `Agent`, assistant `message_end`
is a barrier before tool preflight, so `beforeToolCall` sees state that already
includes the tool-requesting assistant message — important for auditable Azure
calls. Raw `agentLoop()`/`agentLoopContinue()` are observational streams that do
NOT wait for async handlers before later phases.

## Message flow (two hooks)

```
AgentMessage[] → transformContext() → AgentMessage[] → convertToLlm() → Message[] → LLM
                   (optional)                            (required for custom types)
```

- `convertToLlm`: filter UI-only messages, map custom types to `user`/`assistant`/`toolResult`.
  LLMs only understand those three roles.
- `transformContext`: pruning, compaction, external-context injection (see note 4).

## Custom message types

Declaration-merge into `CustomAgentMessages`, then handle in `convertToLlm`
(filter out or map). Use for Lena-only types (e.g. `resource_result`, `chart`)
that render in UI but shouldn't reach the LLM.

```ts
declare module "@earendil-works/pi-agent-core" {
  interface CustomAgentMessages {
    notification: { role: "notification"; text: string; timestamp: number };
  }
}
```

## Events (subscribe for UI/SSE)

`agent_start` → `turn_start` → `message_start`/`message_update`(assistant deltas via
`assistantMessageEvent`)/`message_end` → `tool_execution_start`/`_update`/`_end` →
`turn_end` → `agent_end`.

- `subscribe()` listeners are awaited in registration order.
- `agent_end` = no more loop events; `prompt()`/`waitForIdle()` settle only after
  awaited `agent_end` listeners finish. Good place to flush session state.

## Tools = capability surface

`AgentTool`: `name`, `label`, `description`, TypeBox `parameters`,
`execute(toolCallId, params, signal, onUpdate)`, optional `executionMode`.

- **Throw on failure.** Never return error strings as content — thrown errors
  become tool errors with `isError: true`.
- `onUpdate?.(partial)` streams progress for long-running ops.
- `executionMode: "sequential"` forces the whole batch serial (use for mutations);
  `"parallel"` (default) runs read-only tools concurrently.
- Return `terminate: true` to hint "stop after this batch" (only honored if every
  finalized result in the batch terminates).

## Gate hooks

- `beforeToolCall({ toolCall, args, context })` → `{ block, reason }` to deny
  (gate destructive ops / require confirmation).
- `afterToolCall({ toolCall, result, isError, context })` → patch `details` or set
  `terminate`.

## Steering vs follow-up

- `steer(msg)` — interrupt while tools run; injected after the current turn's tools finish.
- `followUp(msg)` — queued work after the agent would otherwise stop.
- Modes: `"one-at-a-time"` (default) or `"all"`. Clear via `clearSteeringQueue()` /
  `clearFollowUpQueue()` / `clearAllQueues()`.

## Lena mapping

- Lena's agent = an `Agent` instance in `src/backend`.
- Each Azure capability (resource graph, cost, deploy, KQL) = one `AgentTool`.
- Mutations → `executionMode: "sequential"` + `beforeToolCall` confirmation gate.
- Custom render types (charts, resource tables) → `CustomAgentMessages` + `convertToLlm`.
