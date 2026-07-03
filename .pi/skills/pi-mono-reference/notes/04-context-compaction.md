# Note 4 — Context assembly & compaction (DESIGN reference → wire into runtime)

How pi keeps long conversations inside the context window. **Read the concept,
implement Lena's own logic in `transformContext` + a Lena summarizer.** Do not
copy pi's compaction source.

Reference (read-only):
- `packages/agent/README.md` — "Message Flow" (the two-hook pipeline)
- `packages/coding-agent/docs/compaction.md` — auto-compaction + branch summarization
- `packages/agent/src/harness/compaction/` — reference impl:
  `compaction.ts`, `branch-summarization.ts`, `utils.ts`
- `packages/agent/src/agent-loop.ts` — where `transformContext`/`convertToLlm` run

## The pipeline (recap from note 1)

```
AgentMessage[] → transformContext() → AgentMessage[] → convertToLlm() → Message[] → LLM
```

- `transformContext(messages, signal)` — the injection point for compaction /
  pruning / external context. Runs before each LLM call.
- `convertToLlm(messages)` — filter UI-only, map custom → LLM roles.

Low-level callers can also use `shouldStopAfterTurn({ message, toolResults,
context, newMessages })` to stop gracefully at a turn boundary (e.g. "compact
before next turn").

## Compaction concept

**Trigger:** `contextTokens > contextWindow - reserveTokens` (default reserve
16384), or manual `/compact [instructions]`.

**Algorithm:**
1. Walk backward from newest, accumulating token estimates until
   `keepRecentTokens` (default 20000) is reached → this is the cut point.
2. Extract messages from previous kept boundary (or session start) up to the cut.
3. LLM-summarize them (structured format below), passing the previous summary as
   iterative context.
4. Append a `compaction` entry with `summary` + `firstKeptEntryId` + `tokensBefore`.
5. Rebuild context: `system + summary + messages from firstKeptEntryId onward`.

Repeated compactions start the summarized span at the previous compaction's kept
boundary, so surviving messages get re-summarized. `tokensBefore` is recomputed
from the rebuilt context.

**Cut-point rules:** valid cut points = user / assistant / bashExecution / custom
messages. **Never cut at a tool result** (must stay with its tool call).

**Split turns:** when one turn alone exceeds `keepRecentTokens`, cut mid-turn at
an assistant message and merge two summaries (history + turn-prefix).

## Branch summarization concept

On tree navigation away from a branch, summarize the abandoned path and attach a
`branch_summary` entry at the new position:
1. find common ancestor, 2. collect entries old-leaf → ancestor, 3. budget newest-
first, 4. LLM-summarize, 5. append `branch_summary` (`fromId`).

Both mechanisms track **file operations cumulatively** (read/modified files carried
across summaries via entry `details`).

## Structured summary format (both mechanisms)

```
## Goal / ## Constraints & Preferences / ## Progress (Done/In Progress/Blocked)
## Key Decisions / ## Next Steps / ## Critical Context
<read-files>...</read-files>  <modified-files>...</modified-files>
```

Before summarizing, messages are serialized to text via `serializeConversation()`
(`[User]:`, `[Assistant thinking]:`, `[Assistant]:`, `[Assistant tool calls]:`,
`[Tool result]:`) so the model treats it as material to summarize, not a chat to
continue. Tool results are truncated to ~2000 chars.

## Settings (pi defaults, for reference)

`compaction.enabled` (true), `reserveTokens` (16384), `keepRecentTokens` (20000).

## Lena mapping

- Long Azure sessions (big `az`/resource-graph/KQL outputs) overflow context →
  wire a compaction step into Lena's `transformContext`, or trigger via
  `shouldStopAfterTurn` at a turn boundary.
- For Lena, adapt the file-tracking idea into **Azure-resource tracking**
  (touched subscriptions / resource IDs / deployments) carried in summary details.
- Use the structured summary format as a starting template; tune the sections for
  cloud-admin work (e.g. "Resources touched", "Pending mutations").
- Reuse the concept + format. Write Lena's own summarizer call and cut-point logic.
