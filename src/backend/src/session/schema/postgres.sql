-- Session store schema — PostgreSQL (MODE=CLOUD).
-- Same two tables as sqlite.sql, in Postgres idioms: IDENTITY for the transcript
-- sequence, DOUBLE PRECISION for epoch-second timestamps, SMALLINT for the
-- boolean flags (kept as 0/1 to match the SQLite shape and StoredMessage).

-- One durable record per conversation. id is the sessionId used everywhere else.
-- mode + last_interaction_at are the small mutable hot state, updated per turn.
CREATE TABLE IF NOT EXISTS sessions (
    id                  TEXT PRIMARY KEY,
    session_key         TEXT NOT NULL,
    source              TEXT NOT NULL,             -- SessionSource as JSON
    mode                TEXT,                      -- consult|plan|execute|verify
    started_at          DOUBLE PRECISION NOT NULL, -- daily-reset clock
    last_interaction_at DOUBLE PRECISION NOT NULL, -- idle-reset clock
    ended_at            DOUBLE PRECISION,          -- NULL while live
    end_reason          TEXT,
    archived            SMALLINT NOT NULL DEFAULT 0, -- 0/1 boolean
    meta                TEXT NOT NULL DEFAULT '{}'   -- toggles/counters as JSON
);

-- Single source of truth for "who's live": at most one live session per key.
-- Also the index backing getLiveSession(session_key).
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_one_live_per_key
    ON sessions (session_key)
    WHERE ended_at IS NULL;

-- Append-only transcript. id IDENTITY is the per-session sequence when filtered
-- by session_id and ordered by id. content is the AgentMessage as JSON.
CREATE TABLE IF NOT EXISTS messages (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role       TEXT NOT NULL,                      -- user | assistant | toolResult
    content    TEXT NOT NULL,                      -- JSON-serialized AgentMessage
    active     SMALLINT NOT NULL DEFAULT 1,        -- 1 = in live context window
    compacted  SMALLINT NOT NULL DEFAULT 0,        -- 1 = summarized away (still searchable)
    created_at DOUBLE PRECISION NOT NULL
);

-- Live-context reconstruction: getMessages(session_id) WHERE active=1 ORDER BY id.
CREATE INDEX IF NOT EXISTS idx_messages_session_active
    ON messages (session_id, active, id);
