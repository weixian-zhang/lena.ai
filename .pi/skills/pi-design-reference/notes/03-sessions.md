# Note 3 — Sessions (DESIGN reference → build Lena's own store)

How pi persists conversations. **Read the concept, build Lena's own store under
`src/backend`.** Do not vendor pi's `SessionManager`/JSONL code.

Reference (read-only):
- `packages/coding-agent/docs/session-format.md` — JSONL format + full `SessionManager` API
- `packages/coding-agent/docs/sessions.md` — user-facing model (resume, tree, fork, clone)
- `packages/agent/src/harness/session/` — reference implementation:
  - `session.ts`, `jsonl-repo.ts`, `jsonl-storage.ts`, `memory-repo.ts`,
    `memory-storage.ts`, `repo-utils.ts`, `uuid.ts` (`uuidv7`)

## Key design decisions worth carrying over

1. **Append-only JSONL, one JSON object per line.** Each line has a `type`.
   Resumable and replayable by re-reading the file.
2. **Tree, not a flat list.** Entries link via `id` / `parentId` (`parentId: null`
   at root). The current position is the active **leaf**. Branching = new child
   off an earlier entry — in-place, no new file. (Session format v2+; v3 renamed
   `hookMessage` → `custom`.)
3. **Transcript is separate from live `AgentState`.** The session log is the
   durable record; the runtime rebuilds context from it.
4. **Leaf changes are durable entries** (`leaf` / `label`), not in-memory cursors —
   reopening reconstructs position from the log.

## Entry types (from session-format.md)

- `session` (header: version, cwd, optional `parentSession`)
- `message` — wraps an `AgentMessage` (`user` / `assistant` / `toolResult` / extended)
- `model_change`, `thinking_level_change`
- `compaction` (`summary`, `firstKeptEntryId`, `tokensBefore`) — see note 4
- `branch_summary` (`summary`, `fromId`) — see note 4
- `custom` — extension state, NOT sent to LLM
- `custom_message` — extension message that IS sent to LLM (`display` flag)
- `label`, `session_info` (display name)

## AgentMessage content blocks

`TextContent`, `ImageContent`, `ThinkingContent`, `ToolCall`. Base roles: `user`,
`assistant` (has `usage`, `stopReason`, provider/model), `toolResult`
(`toolCallId`, `isError`, `details`). Coding-agent extends with `bashExecution`,
`custom`, `branchSummary`, `compactionSummary` — Lena defines its own extensions
similarly (see note 1, custom message types).

## Context building

`buildSessionContext()` walks leaf → root, then:
1. collects path entries, extracts current model + thinking level,
2. if a `compaction` entry is on the path: emit summary first, then messages from
   `firstKeptEntryId` onward,
3. converts `branch_summary` / `custom_message` to LLM message form.

## SessionManager API surface (reference for Lena's own store shape)

- Create: `create`, `open`, `continueRecent`, `inMemory`, `forkFrom`
- List: `list`, `listAll`
- Append (returns entry id): `appendMessage`, `appendModelChange`,
  `appendThinkingLevelChange`, `appendCompaction`, `appendCustomEntry`,
  `appendCustomMessageEntry`, `appendLabelChange`, `appendSessionInfo`
- Tree nav: `getLeafId`, `getBranch`, `getTree`, `getChildren`, `branch`,
  `branchWithSummary`, `createBranchedSession`, `resetLeaf`
- Context/info: `buildSessionContext`, `getEntries`, `getHeader`, `getSessionId`,
  `getCwd`, `isPersisted`

Storage location in pi: `~/.pi/agent/sessions/--<path>--/<timestamp>_<uuid>.jsonl`.

## Lena mapping

- Build a Lena session store (own module, own path scheme) using the same
  **append-only JSONL + tree** shape. Reuse the *design*, not the files.
- Keep sessions replayable so they can feed `src/evaluation/*.yaml`.
- Store Azure-relevant metadata (subscription, tenant, resource scope) as
  `custom` entries (state) or `custom_message` (context), mirroring pi's split.
