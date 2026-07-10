import type { AgentTool } from "@mariozechner/pi-agent-core";
import { bashTool } from "./bash/bash.js";

/**
 * Tool registry — the Azure surface Lena acts through.
 *
 * Each capability (resource graph, cost, deploy, KQL, bash, ...) becomes one tool here.
 * Contract (see CLAUDE.md): tools throw on failure, never return error strings as content,
 * and expose NO delete/remove capability — deletion is gated out by design.
 *
 * `bash` is the primary surface: a single shell with the Azure CLI pre-authenticated.
 * Narrower typed tools (e.g. Resource Graph) land alongside it as needs arise.
 */
export const tools: AgentTool[] = [bashTool];
