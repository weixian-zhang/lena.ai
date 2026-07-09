import type { AgentTool } from "@mariozechner/pi-agent-core";

/**
 * Tool registry — the Azure surface Lena acts through.
 *
 * Each capability (resource graph, cost, deploy, KQL, bash, ...) becomes one tool here.
 * Contract (see CLAUDE.md): tools throw on failure, never return error strings as content,
 * and expose NO delete/remove capability — deletion is gated out by design.
 *
 * Empty for now; tools land incrementally.
 */
export const tools: AgentTool[] = [];
