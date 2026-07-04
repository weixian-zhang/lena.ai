# Note 6 — Backend/frontend split & streaming (DESIGN reference)

How pi keeps provider creds server-side while streaming to a browser. **Reference
for Lena's `src/backend` ↔ `src/frontend` boundary.** Build Lena's own transport;
`streamProxy` itself is a `pi-agent-core` export you *may* use directly.

Reference (read-only):
- `packages/agent/README.md` — "Proxy Usage" + "Event Flow"
- `packages/agent/src/proxy.ts` — `streamProxy`, `ProxyStreamOptions`,
  `ProxyAssistantMessageEvent` (bandwidth-stripped delta events)

## The idea

Browser must never hold provider API keys. So:

```
frontend (browser)  ──HTTP/SSE/WS──►  backend (holds creds, runs Agent)  ──►  LLM provider
```

`pi-agent-core` ships `streamProxy` as a drop-in `streamFn`: the backend proxies
provider calls, strips the `partial` field from delta events to save bandwidth,
and the client reconstructs the partial message.

```ts
import { Agent, streamProxy } from "@earendil-works/pi-agent-core";

const agent = new Agent({
  streamFn: (model, context, options) =>
    streamProxy(model, context, { ...options, authToken, proxyUrl }),
});
```

`ProxyAssistantMessageEvent` types (proxy.ts): `start`, `text_start/delta/end`,
`thinking_start/delta/end`, `toolcall_start/delta/end`, `done`, `error` — the
wire format between server and browser.

## Two placements for Lena

1. **`Agent` in the backend, thin frontend.** Backend owns the `Agent`, creds,
   tools; frontend sends prompts and receives streamed `AgentEvent`s over SSE/WS.
   Lena maps events → its own UI protocol. (Recommended for Lena — Azure tools
   and creds must stay server-side.)
2. **`Agent` in the browser + `streamProxy`.** Only the LLM transport is proxied;
   the agent loop runs client-side. Less suitable for Lena because Azure tool
   execution needs backend creds.

Lena will typically want **(1)**: keep the `Agent` and all Azure tool execution in
`src/backend`, stream results out.

## Event → UI mapping (from README "Event Flow")

Subscribe on the backend `Agent`, forward as SSE/WS frames:

```
agent_start        → turn_start (session boundary)
turn_start         → turn_start
message_update     → text/thinking deltas (assistantMessageEvent.delta)
tool_execution_*   → tool status (start / streaming update / end)
message_end        → finalized message
agent_end          → done  (flush session here — awaited listeners settle first)
```

Tool execution modes matter for the frontend: in `parallel` mode
`tool_execution_end` events arrive in completion order, but persisted toolResult
messages stay in assistant source order — the UI should key tool cards by
`toolCallId`, not arrival order.

## Lena mapping

- `src/backend`: hosts `Agent` + Azure creds + tools; subscribes to `AgentEvent`s
  and relays them over SSE/WebSocket.
- `src/frontend`: renders the relayed events; never sees provider or Azure creds.
- If Lena ever runs the agent loop in a browser context, use `streamProxy` so keys
  stay on the server — but prefer backend-owned `Agent` for Azure work.
- Design the wire protocol from the `AgentEvent` shape; don't copy pi's transport.
