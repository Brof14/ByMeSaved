from typing import Any

from app.db.database import pool

async def upsert_user(user_id: int, username: str | None, first_name: str | None):
    await pool().execute(
        """INSERT INTO users(id, username, first_name) VALUES($1,$2,$3)
           ON CONFLICT(id) DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name""",
        user_id, username, first_name,
    )

async def create_note(user_id: int, content: str, source_chat_id: int | None,
                      source_message_id: int | None, source_url: str | None) -> int:
    return await pool().fetchval(
        """INSERT INTO notes(user_id, content, source_chat_id, source_message_id, source_url)
           VALUES($1,$2,$3,$4,$5) RETURNING id""",
        user_id, content, source_chat_id, source_message_id, source_url,
    )

async def update_note_ai(note_id: int, title: str, summary: str, category: str,
                         note_type: str, tags: list[str], embedding: list[float]):
    await pool().execute(
        """UPDATE notes SET title=$2, summary=$3, category=$4, note_type=$5, tags=$6, embedding=$7::vector
           WHERE id=$1""",
        note_id, title, summary, category, note_type, tags, str(embedding),
    )

async def get_note(note_id: int, user_id: int):
    row = await pool().fetchrow("SELECT * FROM notes WHERE id=$1 AND user_id=$2", note_id, user_id)
    if row:
        await pool().execute(
            "UPDATE notes SET last_opened_at=now(), open_count=open_count+1 WHERE id=$1", note_id
        )
    return row

async def delete_note(note_id: int, user_id: int) -> None:
    await pool().execute("DELETE FROM notes WHERE id=$1 AND user_id=$2", note_id, user_id)

async def search_notes(user_id: int, query: str, embedding: list[float], limit: int = 8):
    return await pool().fetch(
        """WITH semantic AS (
            SELECT id, 1 - (embedding <=> $2::vector) AS semantic_score
            FROM notes WHERE user_id=$1 AND embedding IS NOT NULL
            ORDER BY embedding <=> $2::vector LIMIT 40
        ), lexical AS (
            SELECT n.id,
                   ts_rank_cd(to_tsvector('simple', coalesce(n.content,'') || ' ' || coalesce(n.title,'') || ' ' || coalesce(n.summary,'') || ' ' || array_to_string(n.tags,' ')), plainto_tsquery('simple',$3)) AS lexical_score
            FROM notes n WHERE n.user_id=$1
        )
        SELECT n.*, COALESCE(s.semantic_score,0) AS semantic_score,
               COALESCE(l.lexical_score,0) AS lexical_score,
               (COALESCE(s.semantic_score,0)*0.75 + LEAST(COALESCE(l.lexical_score,0),1)*0.25) AS score
        FROM notes n
        LEFT JOIN semantic s ON s.id=n.id
        LEFT JOIN lexical l ON l.id=n.id
        WHERE n.user_id=$1 AND (s.id IS NOT NULL OR l.lexical_score > 0)
        ORDER BY score DESC, n.created_at DESC
        LIMIT $4""",
        user_id, str(embedding), query, limit,
    )

async def list_notes(user_id: int, limit: int = 50):
    return await pool().fetch(
        "SELECT * FROM notes WHERE user_id=$1 ORDER BY created_at DESC LIMIT $2", user_id, limit
    )

async def count_notes(user_id: int) -> int:
    return await pool().fetchval("SELECT count(*) FROM notes WHERE user_id=$1", user_id)

async def list_category_counts(user_id: int):
    return await pool().fetch(
        """SELECT COALESCE(category, 'other') AS category, count(*) AS count
           FROM notes WHERE user_id=$1 GROUP BY category ORDER BY count DESC""",
        user_id,
    )
