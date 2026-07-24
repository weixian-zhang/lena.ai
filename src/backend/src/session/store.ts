import type {
  CompactionResult,
  GetMessagesOptions,
  NewMessage,
  NewSession,
  Session,
  SessionEndReason,
  SessionPatch,
  TranscriptMessage,
} from "./types.js";

/**
 * Backend-neutral session store contract.
 *
 * One interface, two implementations: SQLite for `MODE=LOCAL`, PostgreSQL for
 * `MODE=CLOUD`. Callers depend only on this interface — the driver never leaks.
 *
 * Two tables:
 *  - Sessions: durable conversation records + the small mutable hot state
 *    (`mode`, `lastInteractionAt`). A partial unique index on `session_key WHERE
 *    ended_at IS NULL` makes this the single source of truth for the live session.
 *  - Messages: append-only transcript + in-place compaction via `compacted_by_id`
 *    (NULL = live; else the id of the summary that replaced the row).
 *
 * Implementation contract:
 *  - `appendMessages` and `compact` MUST be atomic (single transaction each).
 *  - `getMessages` MUST order by `id` (insertion order), never by timestamp —
 *    wall clocks can regress and scramble turns.
 *  - `createSession` MUST fail if a live session already exists for the key
 *    (the partial unique index enforces this) — end the old one first to reset.
 *  - All timestamps are epoch **seconds** (float), matching the schema.
 */
export interface SessionStore {
  /** Apply the DDL for this backend if not already present. Idempotent. */
  migrate(): Promise<void>;

  // ── Sessions (durable records + live-session lookup) ────────────────────

  /** Create a new session record. `id` must be caller-minted (uuidv7). */
  createSession(input: NewSession): Promise<Session>;

  /** Fetch a session by `sessionId`, or `null` if unknown. */
  getSession(id: string): Promise<Session | null>;

  /**
   * The live session for a routing key (`ended_at IS NULL`), or `null` if none.
   * The partial unique index guarantees at most one. This is the per-message
   * "which session am I in" lookup.
   */
  getLiveSession(sessionKey: string): Promise<Session | null>;

  /** Update hot state (idle clock, mode) on the live session. */
  touchSession(id: string, patch: SessionPatch): Promise<void>;

  /** Mark a session no longer live. Idempotent; keeps the row and its transcript. */
  endSession(id: string, reason: SessionEndReason): Promise<void>;

  // ── Messages (append-only transcript) ───────────────────────────────────

  /**
   * Append messages to a session's transcript in one transaction, assigning
   * autoincrement ids. Intended to be called once per agent turn with the batch
   * from pi's `agent_end` event. Returns the persisted rows (with ids).
   */
  appendMessages(sessionId: string, messages: NewMessage[]): Promise<TranscriptMessage[]>;

  /**
   * Load transcript rows, ordered by `id`. Defaults to live context only
   * (`compacted_by_id IS NULL`); the returned `payload`s feed pi's `initialState.messages`.
   */
  getMessages(sessionId: string, opts?: GetMessagesOptions): Promise<TranscriptMessage[]>;

  /**
   * In-place compaction, atomically:
   *   1. insert `summary` as fresh live rows (the summary head is the first),
   *   2. point every prior live row's `compacted_by_id` at the summary head.
   * Live context after this is `getMessages(id)` (rows with `compacted_by_id IS NULL`);
   * the `sessionId` never rotates. A summary of many rounds forms a walkable chain.
   */
  compact(sessionId: string, summary: NewMessage[]): Promise<CompactionResult>;

  /** Release any pooled connections / file handles. */
  close(): Promise<void>;
}

/**
 * Factory contract. Given the runtime mode, return the matching {@link SessionStore}.
 * Implemented in `sqlite-store.ts` / `postgres-store.ts`; selected here by `MODE`.
 */
export type CreateSessionStore = (opts: {
  mode: "LOCAL" | "CLOUD";
  /** SQLite file path (LOCAL) or Postgres connection string (CLOUD). */
  connection: string;
}) => Promise<SessionStore>;
