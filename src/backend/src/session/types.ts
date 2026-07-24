import type { AgentMessage, AgentMode } from "../agent/types.js";
import type { InboundMessage } from "../gateway/types.js";

/**
 * Domain types for the session store.
 *
 * Two tables:
 *  - `sessions` — one durable record per conversation (a `sessionId`), plus the
 *    small amount of mutable hot state (mode, idle clock). A partial unique index
 *    on `session_key WHERE ended_at IS NULL` makes it the single source of truth
 *    for "which session is live" — no separate routing table to keep in sync.
 *  - `messages` — append-only transcript, one row per {@link AgentMessage}.
 *
 * The runtime (pi-agent-core) never sees these types directly: a session is
 * hydrated by loading `messages` for the live `sessionId` and passing them as
 * `initialState.messages`, and persisted by appending new messages per turn.
 */

/** Backend selection. Sourced from the `MODE` env var (`LOCAL` → SQLite, `CLOUD` → Postgres). */
export type StoreMode = "LOCAL" | "CLOUD";

/**
 * Transcript row role. Mirrors pi's {@link AgentMessage} base roles; a compaction
 * summary is stored as an ordinary message row (a live row that other, older rows
 * now point at via `compactedById`).
 */
export type MessageRole = "user" | "assistant" | "toolResult";

/**
 * Why a session stopped being the live one for its key. Terminal vs recoverable
 * is a property of this enum: `manual`, `idle_timeout`, and `daily_reset` mint a
 * *fresh* successor under the same key; `agent_close` is bookkeeping.
 */
export type SessionEndReason =
  | "manual" // user asked for a new session (e.g. /new)
  | "idle_timeout" // no interaction past the idle window
  | "daily_reset" // crossed the daily reset hour
  | "agent_close"; // process/gateway shut the session down

/**
 * A durable conversation record. `id` is the `sessionId` referenced everywhere
 * else. Carries the small mutable hot state (`mode`, `lastInteractionAt`) inline
 * — updated per turn via {@link SessionStore.touchSession}.
 */
export type Session = {
  /** uuidv7, caller-minted. Doubles as the transcript's foreign key. */
  id: string;
  /** Routing key this session was created for. At most one live session per key. */
  sessionKey: string;
  source: InboundMessage;
  /** Current conversational mode; `null` until set. */
  mode: AgentMode | null;
  /** Start of this session — drives the daily reset. */
  startedAt: number;
  /** Last real user turn — drives the idle reset. Not bumped by cron/system turns. */
  lastInteractionAt: number;
  /** Set when this session is no longer live; `null` while live. */
  endedAt: number | null;
  endReason: SessionEndReason | null;
};

/** Input to {@link SessionStore.createSession}. Store fills defaults for omitted fields. */
export type NewSession = {
  id: string;
  sessionKey: string;
  source: InboundMessage;
  mode?: AgentMode;
  /** Defaults to now (epoch seconds); also seeds `lastInteractionAt`. */
  startedAt?: number;
};

/** Fields {@link SessionStore.touchSession} may update on the live session. */
export type SessionPatch = {
  lastInteractionAt?: number;
  mode?: AgentMode;
};

/** A persisted transcript row. `id` is monotonic per store; ordering key within a session. */
export type TranscriptMessage = {
  /** Autoincrement id. When filtered by `sessionId` and ordered by `id`, this *is* the sequence. */
  id: number;
  sessionId: string;
  /** Denormalized from `payload.role` for cheap filtering. */
  role: MessageRole;
  /** The full pi message, round-tripped losslessly (stored as JSON in `content`). */
  payload: AgentMessage;
  /**
   * Liveness + compaction lineage in one field:
   *  - `null` → live (in the context window; `WHERE compacted_by_id IS NULL` reconstructs it).
   *  - `<id>` → summarized away; the id of the summary message that replaced this row.
   * See {@link SessionStore.compact}.
   */
  compactedById: number | null;
  createdAt: number;
};

/** Input to {@link SessionStore.appendMessages} / {@link SessionStore.compact}. */
export type NewMessage = {
  role: MessageRole;
  payload: AgentMessage;
  /** Defaults to now (epoch seconds). */
  createdAt?: number;
};

/** Options for {@link SessionStore.getMessages}. */
export type GetMessagesOptions = {
  /** Include compacted (`compacted_by_id IS NOT NULL`) rows. Default `false` → live context only. */
  includeInactive?: boolean;
  /** Max rows to return, ordered by `id`. */
  limit?: number;
  /** Rows to skip (pagination). */
  offset?: number;
};

/** Result of a {@link SessionStore.compact} call. */
export type CompactionResult = {
  /** How many previously-live rows were summarized away (pointed at the summary head). */
  archivedCount: number;
  /** The freshly inserted summary rows (now the head of the live context). */
  summary: TranscriptMessage[];
};
