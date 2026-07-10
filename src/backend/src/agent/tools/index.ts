import type { AgentTool } from "@mariozechner/pi-agent-core";
import { azureCliGenerateTool } from "./azure-cli/azure-cli.js";
import { bashTool } from "./bash/bash.js";

/**
 * Tool registry — the Azure surface Lena acts through.
 *
 * Each capability (resource graph, cost, deploy, KQL, bash, ...) becomes one tool here.
 * Contract (see CLAUDE.md): tools throw on failure, never return error strings as content,
 * and expose NO delete/remove capability — deletion is gated out by design.
 *
 * `bash` is the primary surface: a single shell with the Azure CLI pre-authenticated.
 * `azure_cli_generate` turns a natural-language intent into the exact `az` command
 * (via Azure's own MCP server) for `bash` to then run. Narrower typed tools (e.g.
 * Resource Graph) land alongside them as needs arise.
 */
export const tools: AgentTool[] = [bashTool, azureCliGenerateTool];
