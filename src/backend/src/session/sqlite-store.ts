import { readFileSync } from "node:fs";
import { join } from "node:path";
import Database from "better-sqlite3";
import type { AgentMessage, AgentMode } from "../agent/types.js";
import type { InboundMessage } from "../gateway/types.js";
import type { SessionStore } from "./store.js";
import type {
  CompactionBoundary,
  CompactionResult,
  GetMessagesOptions,
  MessageRole,
  NewMessage,
  NewSession,
  Session,
  SessionEndReason,
  SessionPatch,
  TranscriptMessage,
} from "./types.js";

/** Epoch seconds (float), matching the schema's REAL timestamps. */
function nowSec(): number {
  return Date.now() / 1000;
}

/** better-sqlite3 tags constraint errors with a `SQLITE_CONSTRAINT_*` code. */
function isUniqueViolation(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  const code = (err as { code?: unknown }).code;
  return code === "SQLITE_CONSTRAINT_UNIQUE" || code === "SQLITE_CONSTRAINT_PRIMARYKEY";
}

/** Raw `sessions` row as SQLite hands it back (snake_case, flags/JSON unparsed). */
type SessionRow = {
  id: string;
  session_key: string;
  source: string;
  mode: string | null;
  started_at: number;
  last_interaction_at: number;
  ended_at: number | null;
  end_reason: string | null;
};

/** Raw `messages` row. SQLite has no boolean, so `is_summary` comes back as 0/1. */
type MessageRow = {
  id: number;
  session_id: string;
  role: string;
  content: string;
  seq: number;
  is_summary: number;
  created_at: number;
  compacted_by_id: number | null;
};

function toSession(r: SessionRow): Session {
  return {
    id: r.id,
    sessionKey: r.session_key,
    source: JSON.parse(r.source) as InboundMessage,
    mode: r.mode as AgentMode | null,
    startedAt: r.started_at,
    lastInteractionAt: r.last_interaction_at,
    endedAt: r.ended_at,
    endReason: r.end_reason as SessionEndReason | null,
  };
}

function toMessage(r: MessageRow): TranscriptMessage {
  return {
    id: r.id,
    sessionId: r.session_id,
    seq: r.seq,
    role: r.role as MessageRole,
    payload: JSON.parse(r.content) as AgentMessage,
    isSummary: r.is_summary === 1,
    compactedById: r.compacted_by_id,
    createdAt: r.created_at,
  };
}

/**
 * SQLite {@link SessionStore} (MODE=LOCAL), backed by better-sqlite3.
 *
 * better-sqlite3 is synchronous; each method wraps a sync call so the async
 * interface stays uniform with the Postgres impl. Multi-row writes go through
 * `db.transaction(...)` to satisfy the atomicity clauses of the contract.
 */
export class SqliteSessionStore implements SessionStore {
  private readonly db: Database.Database;

  constructor(connection: string) {
    this.db = new Database(connection);
    // WAL for concurrent readers; enforce FKs; wait rather than fail on a busy lock.
    this.db.pragma("journal_mode = WAL");
    this.db.pragma("foreign_keys = ON");
    this.db.pragma("busy_timeout = 5000");
  }

  async migrate(): Promise<void> {
    const ddl = readFileSync(join(import.meta.dirname, "schema", "sqlite.sql"), "utf8");
    this.db.exec(ddl);
  }

  // ── Sessions ────────────────────────────────────────────────────────────

  async createSession(input: NewSession): Promise<Session> {
    const startedAt = input.startedAt ?? nowSec();
    const mode = input.mode ?? null;
    try {
      this.db
        .prepare(
          `INSERT INTO sessions
             (id, session_key, source, mode, started_at, last_interaction_at, ended_at, end_reason)
           VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)`,
        )
        .run(input.id, input.sessionKey, JSON.stringify(input.source), mode, startedAt, startedAt);
    } catch (err) {
      if (isUniqueViolation(err)) {
        throw new Error(
          `Cannot create session: a live session already exists for key "${input.sessionKey}" ` +
            `(or id "${input.id}"). End the existing one first.`,
        );
      }
      throw err;
    }
    return {
      id: input.id,
      sessionKey: input.sessionKey,
      source: input.source,
      mode,
      startedAt,
      lastInteractionAt: startedAt,
      endedAt: null,
      endReason: null,
    };
  }

  async getSession(id: string): Promise<Session | null> {
    const row = this.db.prepare(`SELECT * FROM sessions WHERE id = ?`).get(id) as
      | SessionRow
      | undefined;
    return row ? toSession(row) : null;
  }

  async getLiveSession(sessionKey: string): Promise<Session | null> {
    const row = this.db
      .prepare(`SELECT * FROM sessions WHERE session_key = ? AND ended_at IS NULL`)
      .get(sessionKey) as SessionRow | undefined;
    return row ? toSession(row) : null;
  }

  async touchSession(id: string, patch: SessionPatch): Promise<void> {
    const sets: string[] = [];
    const vals: (string | number)[] = [];
    if (patch.lastInteractionAt !== undefined) {
      sets.push("last_interaction_at = ?");
      vals.push(patch.lastInteractionAt);
    }
    if (patch.mode !== undefined) {
      sets.push("mode = ?");
      vals.push(patch.mode);
    }
    if (sets.length === 0) return;
    vals.push(id);
    this.db.prepare(`UPDATE sessions SET ${sets.join(", ")} WHERE id = ?`).run(...vals);
  }

  async endSession(id: string, reason: SessionEndReason): Promise<void> {
    // WHERE ended_at IS NULL makes this idempotent — a re-end keeps the first reason/time.
    this.db
      .prepare(`UPDATE sessions SET ended_at = ?, end_reason = ? WHERE id = ? AND ended_at IS NULL`)
      .run(nowSec(), reason, id);
  }

  // ── Messages ──────────────────────────────────────────────────────────────

  async appendMessages(sessionId: string, messages: NewMessage[]): Promise<TranscriptMessage[]> {
    if (messages.length === 0) return [];
    const insert = this.db.prepare(
      `INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)`,
    );
    // seq = id for ordinary appends. Set in a second statement rather than a
    // subquery so the value comes from the sequence itself and can't race.
    const setSeq = this.db.prepare(`UPDATE messages SET seq = id WHERE id = ?`);
    const tx = this.db.transaction((batch: NewMessage[]): TranscriptMessage[] => {
      const out: TranscriptMessage[] = [];
      for (const m of batch) {
        const createdAt = m.createdAt ?? nowSec();
        const info = insert.run(sessionId, m.role, JSON.stringify(m.payload), createdAt);
        const id = Number(info.lastInsertRowid);
        setSeq.run(id);
        out.push({
          id,
          sessionId,
          seq: id,
          role: m.role,
          payload: m.payload,
          isSummary: false,
          compactedById: null,
          createdAt,
        });
      }
      return out;
    });
    return tx(messages);
  }

  async getMessages(sessionId: string, opts: GetMessagesOptions = {}): Promise<TranscriptMessage[]> {
    let sql = `SELECT * FROM messages WHERE session_id = ?`;
    const vals: (string | number)[] = [sessionId];
    if (!opts.includeInactive) sql += ` AND compacted_by_id IS NULL`;
    sql += ` ORDER BY seq, id`; // conversation order — never timestamp
    if (opts.limit !== undefined) {
      sql += ` LIMIT ?`;
      vals.push(opts.limit);
    }
    if (opts.offset !== undefined) {
      // SQLite requires a LIMIT before OFFSET; -1 means unbounded.
      if (opts.limit === undefined) sql += ` LIMIT -1`;
      sql += ` OFFSET ?`;
      vals.push(opts.offset);
    }
    const rows = this.db.prepare(sql).all(...vals) as MessageRow[];
    return rows.map(toMessage);
  }

  async compact(
    sessionId: string,
    summary: NewMessage,
    boundary: CompactionBoundary,
  ): Promise<CompactionResult> {
    const insert = this.db.prepare(
      `INSERT INTO messages (session_id, role, content, seq, is_summary, created_at)
       VALUES (?, ?, ?, ?, 1, ?)`,
    );
    // Archive by conversation-order span. `id <> ?` keeps the summary just
    // inserted — whose seq is inside the span by construction — from archiving
    // itself. Concurrent appends land above beforeSeq and are left alone.
    const archiveStmt = this.db.prepare(
      `UPDATE messages SET compacted_by_id = ?
       WHERE session_id = ? AND compacted_by_id IS NULL AND id <> ?
         AND seq > ? AND seq < ?`,
    );
    const tx = this.db.transaction((): CompactionResult => {
      const createdAt = summary.createdAt ?? nowSec();
      const info = insert.run(
        sessionId,
        summary.role,
        JSON.stringify(summary.payload),
        boundary.seq,
        createdAt,
      );
      const id = Number(info.lastInsertRowid);
      const archivedCount = archiveStmt.run(
        id,
        sessionId,
        id,
        boundary.afterSeq,
        boundary.beforeSeq,
      ).changes;

      // A stale boundary would leave a summary describing nothing. Throwing
      // rolls the insert back with it.
      if (archivedCount === 0) {
        throw new Error(
          `compact: no live rows in (${boundary.afterSeq}, ${boundary.beforeSeq}) ` +
            `for session ${sessionId}`,
        );
      }

      return {
        archivedCount,
        summary: {
          id,
          sessionId,
          seq: boundary.seq,
          role: summary.role,
          payload: summary.payload,
          isSummary: true,
          compactedById: null,
          createdAt,
        },
      };
    });
    return tx();
  }

  async close(): Promise<void> {
    this.db.close();
  }
}

/** Convenience factory: open, migrate, and return a ready store for MODE=LOCAL. */
export async function createSqliteSessionStore(connection: string): Promise<SessionStore> {
  const store = new SqliteSessionStore(connection);
  await store.migrate();
  return store;
}
