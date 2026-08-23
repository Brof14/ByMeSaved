CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    category TEXT,
    note_type TEXT,
    tags TEXT[] NOT NULL DEFAULT '{}',
    source_chat_id BIGINT,
    source_message_id BIGINT,
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_opened_at TIMESTAMPTZ,
    open_count INTEGER NOT NULL DEFAULT 0,
    embedding vector(2048)
);

CREATE INDEX IF NOT EXISTS notes_user_created_idx ON notes(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS notes_user_category_idx ON notes(user_id, category);
CREATE OR REPLACE FUNCTION notes_tsvector(content text, title text, summary text, tags text[])
RETURNS tsvector AS $func$
    SELECT to_tsvector('simple'::regconfig,
        coalesce(content,'') || ' ' || coalesce(title,'') || ' ' || coalesce(summary,'') || ' ' || array_to_string(tags,' ')
    );
$func$ LANGUAGE sql IMMUTABLE PARALLEL SAFE;

CREATE INDEX IF NOT EXISTS notes_fts_idx ON notes USING GIN (
    notes_tsvector(content, title, summary, tags)
);
CREATE INDEX IF NOT EXISTS notes_embedding_idx ON notes USING hnsw (embedding vector_cosine_ops);
