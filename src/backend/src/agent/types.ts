import type { AgentMessage as PiAgentMessage } from "@mariozechner/pi-agent-core";

/**
 * Lena's transcript message type.
 *
 * Structurally pi's `AgentMessage` — so it stays assignable to the pi `Agent`'s
 * `initialState.messages` and `transformContext` with zero adapter code — but
 * owned and named here. This file is the *only* place that imports the pi type;
 * the rest of the app depends on Lena's `AgentMessage`, not on
 * `@mariozechner/pi-agent-core`. If the agent framework ever changes, re-point
 * (or redefine) this one alias instead of touching every consumer.
 */
export type AgentMessage = PiAgentMessage;

/**
 * Lena's conversational mode — drives the prompt stack (`base + modePrompt(mode)`).
 * Persisted on the session so a resumed conversation keeps its mode.
 */
export type AgentMode = "plan" | "eyes-wide-shut";
