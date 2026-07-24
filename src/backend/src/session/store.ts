import type {
  CompactionResult,
  GetMessagesOptions,
  NewMessage,
  NewSession,
  Session,
  SessionEndReason,
  SessionPatch,
  StoredMessage,
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
 *  - Messages: append-only transcript + in-place, soft-archive compaction.
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

  /** Update hot state (idle clock, mode, meta) on the live session. */
  touchSession(id: string, patch: SessionPatch): Promise<void>;

  /** Mark a session no longer live. Idempotent; keeps the row and its transcript. */
  endSession(id: string, reason: SessionEndReason): Promise<void>;

  /** Archive/unarchive a session for listing/pruning (does not end it). */
  setArchived(id: string, archived: boolean): Promise<void>;

  // ── Messages (append-only transcript) ───────────────────────────────────

  /**
   * Append messages to a session's transcript in one transaction, assigning
   * autoincrement ids. Intended to be called once per agent turn with the batch
   * from pi's `agent_end` event. Returns the persisted rows (with ids).
   */
  appendMessages(sessionId: string, messages: NewMessage[]): Promise<StoredMessage[]>;

  /**
   * Load transcript rows, ordered by `id`. Defaults to live context only
   * (`active = 1`); the returned `payload`s feed pi's `initialState.messages`.
   */
  getMessages(sessionId: string, opts?: GetMessagesOptions): Promise<StoredMessage[]>;

  /**
   * In-place compaction (Hermes `archive_and_compact`), atomically:
   *   1. soft-archive every current live row (`active = 0, compacted = 1`),
   *   2. insert `summary` as fresh `active = 1` rows.
   * The `sessionId` never rotates; live context after this is `getMessages(id)`.
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
