# CLAUDE.md

Guidance for Claude Code in this repo.

## What this is

Lena = Azure cloud expert agent. User chats in natural language; Lena does everything on Azure:
design, provisioning, troubleshooting (apps + config), operations (patch mgmt, monitoring, more).
End-to-end execution: resource search, data analysis, ETL, deploy, Sentinel threat hunting, etc.
**Never deletes Azure resources** — out of scope by design; decline or escalate instead.

## Tech stack

- Node.js latest (LTS/current) + TypeScript. Modern built-ins: native fetch, `node:` imports, ESM.
  Runtime code → `src/backend`.
- Backend-only for now. No UI code. Keep streamed event channel contract clean so frontend can
  attach later.
- Backend hosted on Azure. Config/secrets/provider selection injectable via env/config, not baked in.
- Python, az CLI, other binaries = runtime tools the agent shells out to (bash tool / Azure MCP),
  not the app language.
- Greenfield: `src/backend` empty, no package.json/build/lint/test yet. You're establishing
  conventions, not following them. Prior discarded approach: git history of
  `feat/task_runner_overseer`.

## Where the design lives (read before building)

Little code exists; architecture = reference repos + skills + eval specs.

1. `.claude/skills/` — two design-reference skills, keyword-gated, reference material not designs
   to copy:
   - `pi-design-reference` (trigger `ref-pi`) — Pi monorepo as prior art. `pi-agent-core` /
     `pi-ai` = npm **dependencies** (call APIs, never vendor/fork); Pi harness = design reference
     to reimplement under `src/backend`. Non-negotiable: no hardcoded model provider — agent takes
     a `Model`, provider from config/env.
   - `openclaw-design-reference` (trigger `ref-openclaw`) — OpenClaw as one informed opinion;
     extract principles, adapt, simplify where heavier than Lena needs.
2. `src/evaluation/*.yaml` — behavioral spec / acceptance criteria. Each YAML = category of e2e
   test prompts (`resource_search_prompt.yaml`, `data_analysis_prompt.yaml`,
   `sentinel_threat_hunting_prompt.yaml`, `build_app_and_deploy.yaml`,
   `no_such_feature_prompt.yaml`). Keep sessions replayable to drive these evals.

## Reference codebases

Read-only prior art, inspiration only. Don't copy designs/code. Challenge their approaches — if
heavier/weaker/poor fit, say so and adopt better solution. Disagreeing is expected.

- OpenClaw — `/Users/weixianzhang/projects/open_source/openclaw`
- Pi mono — `/Users/weixianzhang/projects/open_source/pi`

Read both for (compare takes):

- Agent harness — loop, execution env abstraction, run lifecycle/phases.
- Context assembly — context window budgeting per run (system prompt, history, tool schemas),
  compaction/pruning.
- Session management — persistence (append-only JSONL trees), forking/replay, isolation.
- Channels — deterministic routing: inbound message → agent + session key. Model never picks
  channel.
- Gateway — transport layer (e.g. WebSocket) fronting all channels, separate from agent logic.

`ref-pi` / `ref-openclaw` skills have file maps + distilled notes per concern.

## Architecture principles (load-bearing)

- **Provider-agnostic.** Never hardcode model provider. `docs/environment_packages.md` lists AI
  Foundry env vars, but provider comes from config/env, not code.
- **Reference, don't copy — challenge.** Read concept, write Lena's own version; prefer better
  approaches over the reference. Cite source file for patterns, or note why diverged.
- **Backend/frontend split (frontend deferred).** Creds + agent loop server-side; future frontend
  talks over streamed event channel — creds never reach browser.
- **No deletion — hard boundary.** Design → provisioning → operations, never delete. No
  delete/remove capability in any tool; gate out deletes exposed by underlying tools (`az`, Azure
  MCP).
- **Tools = the Azure surface.** Each capability (resource graph, cost, deploy, KQL, bash) = a
  tool. Throw on failure, never return error strings as content. Sequential execution mode for
  mutations. HITL confirmation for destructive/stateful ops short of deletion (stop, scale-down,
  etc.).
- **Sequential, supervised execution with reflection.** Task-steps in order under a supervisor,
  bounded reflection loop, HITL escalation — not a free-form loop.
