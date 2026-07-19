import type { AgentTool } from "@mariozechner/pi-agent-core";
import { azureCliGenerateTool } from "./azure-cli/azure-cli.js";
import { bashTool } from "./bash.js";
import { clarifyTool } from "./clarify.js";
import { proposePlanTool } from "./propose-plan.js";

/**
 * Tool registry — the Azure surface Lena acts through.
 *
 * Each capability (resource graph, cost, deploy, KQL, bash, ...) becomes one tool here.
 * Contract (see CLAUDE.md): tools throw on failure, never return error strings as content,
 * and expose NO delete/remove capability — deletion is gated out by design.
 *
 * `bash` is the single execution surface: a shell with the Azure CLI pre-authenticated,
 * plus every other binary on the host (node, python, jq, git).
 * `propose_plan` is the Investigate→Action gate: it presents a plan and ends the run,
 * so mutations only follow an approval. It executes nothing itself.
 * `clarify` asks the user a question (optional pickable choices) and ends the run, so the
 * model resolves genuine ambiguity instead of guessing. Both are terminate-and-resume: the
 * user's next message is the answer.
 * `azure_cli_generate` turns a natural-language intent into the exact `az` command
 * (via Azure's own MCP server) for `bash` to then run. Narrower typed tools (e.g.
 * Resource Graph) land alongside them as needs arise.
 */
export const tools: AgentTool[] = [bashTool, proposePlanTool, clarifyTool, azureCliGenerateTool];
