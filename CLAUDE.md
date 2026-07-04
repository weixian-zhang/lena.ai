# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Lena is your **Azure assistant that does everything for you on Azure** — from design and
provisioning through to day-to-day operations. It takes natural-language requests and carries them
out end to end (resource search, data analysis, ETL, deploy, Sentinel threat hunting, etc.) on the
user's behalf. **The one operation Lena does not perform is deletion** — destructive removal of
Azure resources is out of scope by design; the agent should decline or escalate rather than delete.

## Tech stack

- **Node.js + TypeScript** — the application language for the whole codebase (agent core, tools,
  backend). New runtime code goes under `src/backend` in TypeScript.
- **Backend is hosted on Azure.** Design the backend as an Azure-hosted service; keep
  configuration, secrets, and provider selection injectable via env/config rather than baked in.
- Python, the Azure CLI, and other binaries below are **runtime tools the agent shells out to**
  (e.g. via a bash tool or Azure MCP) — they are not the language the app is written in.

**The implementation is greenfield.** The code was intentionally reset ("remove old codes to start
afresh") and `src/backend` is currently empty. There is no `package.json`, build, lint, or test
tooling in the repo yet. When adding runtime code, you are establishing these conventions, not
following existing ones — check the git history of `feat/task_runner_overseer` for the prior
(discarded) approach before reintroducing a pattern.

## Where the design lives (read before building)

Because there is little code, the intended architecture is captured in the reference repos, the
skills, and the eval specs. Consult them before writing agent code:

1. **`.claude/skills/`** — two design-reference skills, each gated behind a trigger keyword the
   user must type. They are reference material, **not** designs to copy verbatim:
   - **`pi-design-reference`** (trigger: `ref-pi`) — treats the Pi monorepo as prior art.
     Key rule it encodes: `pi-agent-core` / `pi-ai` are npm **dependencies** (call their APIs,
     never vendor/fork), while the Pi harness is a **design reference** to reimplement under
     `src/backend`. Non-negotiable: **no hardcoded model provider** — the agent takes a `Model`;
     provider comes from config/env.
   - **`openclaw-design-reference`** (trigger: `ref-openclaw`) — treats the OpenClaw codebase as
     one informed opinion; extract principles, adapt, simplify where it's heavier than Lena needs.

2. **`src/evaluation/*.yaml`** — the **behavioral spec**. Each YAML is a category of end-to-end
   test cases with natural-language prompts (e.g. `resource_search_prompt.yaml`,
   `data_analysis_prompt.yaml`, `sentinel_threat_hunting_prompt.yaml`,
   `build_app_and_deploy.yaml`, `no_such_feature_prompt.yaml`). Treat these as the acceptance
   criteria for what the agent must handle, and keep sessions replayable so they can drive these
   evals.

## Reference codebases (design + code, as a second opinion)

Two open-source agent codebases are the primary references for how to build Lena's harness. Both
are **read-only prior art** — study the technique and the way they solve a problem, take it as a
**second opinion**, and adapt to Lena. Do **not** blindly copy code or structure wholesale; where a
reference is heavier than Lena needs, simplify and say so.

- **OpenClaw** — `/Users/weixianzhang/projects/open_source/openclaw`
- **Pi mono** — `/Users/weixianzhang/projects/open_source/pi`

Read them specifically for these concerns (both repos have relevant takes to compare):

- **Agent harness** — the loop, execution environment abstraction, run lifecycle/phases.
- **Context assembly** — how the model's context window is budgeted and built each run
  (system prompt, history, tool schemas), plus compaction/pruning of long histories.
- **Session management** — persistence (append-only JSONL trees), forking/replay, isolation.
- **Channels** — the deterministic routing layer that maps inbound messages to an agent + session
  key (the model never picks a channel).
- **Gateway** — the transport layer (e.g. WebSocket) that fronts all channels, kept separate from
  agent logic.

Use the `ref-pi` / `ref-openclaw` skills to navigate these repos; they contain the file maps and
distilled notes for each concern.

## Architecture principles (from the design references)

These are the load-bearing constraints to preserve when implementing:

- **Provider-agnostic.** Never assume or hardcode a model provider anywhere. Even though
  `docs/environment_packages.md` lists AI Foundry env vars, the provider must come from
  config/env, not code.
- **Reference, don't copy.** The Pi and OpenClaw repos (under
  `/Users/weixianzhang/projects/open_source/`) are read-only prior art. Read the concept, then
  write Lena's own version. Cite the source file you drew a pattern from.
- **Backend/frontend split.** Credentials and the agent loop live server-side; the frontend talks
  to the backend over a streamed event channel — creds never reach the browser.
- **No deletion — hard boundary.** Lena covers design → provisioning → operations, but never
  deletes Azure resources. Deletion is out of scope by design: the agent declines or escalates
  rather than issuing a delete. Do not add delete/remove capabilities to any tool, and gate them
  out if an underlying tool (e.g. `az`, Azure MCP) exposes them.
- **Tools = the Azure surface.** Each capability (resource graph, cost, deploy, KQL, bash) is a
  tool that throws on failure (never returns error strings as content), with sequential execution
  mode for mutations and human-in-the-loop confirmation for other destructive/stateful ops (stop,
  scale-down, etc.) that fall short of deletion.
- **Sequential, supervised execution with reflection.** Task-steps run in order under a supervisor
  with a bounded reflection loop and HITL escalation — not a free-form loop.

## Environment & runtime requirements

Documented in `docs/environment_packages.md`. Needed to actually run the agent:

- **Node.js** (latest) — required to `npx` the **Azure MCP Server** for `azcli` tooling.
- **Python 3.13** with `pandas`, `matplotlib`, `seaborn`, `numpy`; **smolagents** `CodeAgent`
  installed via `uv pip install "smolagents[openai]"` plus `ddgs`.
- **Azure CLI** with extensions: `resource-graph`, `log-analytics`, `aks-preview`.
- Environment variables for Azure auth and the LLM endpoint:
  `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`,
  `AZURE_MCP_INCLUDE_PRODUCTION_CREDENTIALS`,
  `AI_FOUNDRY_DEPLOYMENT_ENDPOINT`, `AI_FOUNDRY_DEPLOYMENT_KEY`.

## Working in this repo

- Active development branch is `feat/agent-core`; `main` is the base for PRs.
- The `.claude/skills/` skills are mirrors of `.pi/skills/` (the original source of truth). If you
  change one, keep the other in sync or the two will diverge.
