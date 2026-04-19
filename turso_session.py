from __future__ import annotations

import json

import libsql_client
from agents import SessionSettings
from agents.memory import SessionABC
from agents import TResponseInputItem

SUMMARY_WINDOW = 40  # keep this many recent items verbatim; older items are summarized


def _resolve_limit(limit: int | None, settings: SessionSettings | None) -> int | None:
    if limit is not None:
        return limit
    return settings.limit if settings else None


class TursoSession(SessionABC):
    """Turso-backed session with rolling summarization support."""

    session_settings: SessionSettings | None = None

    def __init__(
        self,
        session_id: str,
        url: str,
        auth_token: str,
        sessions_table: str = "agent_sessions",
        messages_table: str = "agent_messages",
        session_settings: SessionSettings | None = None,
    ):
        self.session_id = session_id
        self.session_settings = session_settings or SessionSettings()
        self.sessions_table = sessions_table
        self.messages_table = messages_table
        self._url = url
        self._auth_token = auth_token

    def _make_client(self) -> libsql_client.Client:
        return libsql_client.create_client(url=self._url, auth_token=self._auth_token)

    async def _ensure_schema(self, client: libsql_client.Client) -> None:
        await client.batch([
            f"""
            CREATE TABLE IF NOT EXISTS {self.sessions_table} (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.messages_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES {self.sessions_table} (session_id)
                    ON DELETE CASCADE
            )
            """,
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self.messages_table}_session_id
            ON {self.messages_table} (session_id, id)
            """,
            """
            CREATE TABLE IF NOT EXISTS agent_summaries (
                session_id TEXT PRIMARY KEY,
                summary_text TEXT NOT NULL,
                summarized_up_to_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ])

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        window = _resolve_limit(limit, self.session_settings) or SUMMARY_WINDOW
        async with self._make_client() as client:
            await self._ensure_schema(client)

            # Fetch summary if one exists
            sum_result = await client.execute(
                libsql_client.Statement(
                    "SELECT summary_text FROM agent_summaries WHERE session_id = ?",
                    [self.session_id],
                )
            )
            summary_text = sum_result.rows[0][0] if sum_result.rows else None

            # Fetch last `window` messages
            msg_result = await client.execute(
                libsql_client.Statement(
                    f"SELECT message_data FROM {self.messages_table} WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    [self.session_id, window],
                )
            )
            items = [json.loads(row[0]) for row in reversed(msg_result.rows)]

            if summary_text:
                summary_item = {
                    "role": "system",
                    "content": f"[Summary of earlier conversation: {summary_text}]",
                }
                return [summary_item] + items  # type: ignore[return-value]
            return items

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        if not items:
            return
        async with self._make_client() as client:
            await self._ensure_schema(client)
            stmts: list = [
                libsql_client.Statement(
                    f"INSERT OR IGNORE INTO {self.sessions_table} (session_id) VALUES (?)",
                    [self.session_id],
                ),
                *[
                    libsql_client.Statement(
                        f"INSERT INTO {self.messages_table} (session_id, message_data) VALUES (?, ?)",
                        [self.session_id, json.dumps(item)],
                    )
                    for item in items
                ],
                libsql_client.Statement(
                    f"UPDATE {self.sessions_table} SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                    [self.session_id],
                ),
            ]
            await client.batch(stmts)

    async def pop_item(self) -> TResponseInputItem | None:
        async with self._make_client() as client:
            await self._ensure_schema(client)
            result = await client.execute(
                libsql_client.Statement(
                    f"SELECT id, message_data FROM {self.messages_table} WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                    [self.session_id],
                )
            )
            if not result.rows:
                return None
            row_id = result.rows[0][0]
            message_data = result.rows[0][1]
            await client.execute(
                libsql_client.Statement(
                    f"DELETE FROM {self.messages_table} WHERE id = ?",
                    [row_id],
                )
            )
            try:
                return json.loads(message_data)
            except json.JSONDecodeError:
                return None

    async def clear_session(self) -> None:
        async with self._make_client() as client:
            await self._ensure_schema(client)
            await client.batch([
                libsql_client.Statement(
                    f"DELETE FROM {self.messages_table} WHERE session_id = ?",
                    [self.session_id],
                ),
                libsql_client.Statement(
                    f"DELETE FROM {self.sessions_table} WHERE session_id = ?",
                    [self.session_id],
                ),
                libsql_client.Statement(
                    "DELETE FROM agent_summaries WHERE session_id = ?",
                    [self.session_id],
                ),
            ])

    # ── Summarization helpers ─────────────────────────────────

    async def get_message_count(self) -> int:
        async with self._make_client() as client:
            await self._ensure_schema(client)
            result = await client.execute(
                libsql_client.Statement(
                    f"SELECT COUNT(*) FROM {self.messages_table} WHERE session_id = ?",
                    [self.session_id],
                )
            )
            return int(result.rows[0][0]) if result.rows else 0

    async def get_existing_summary(self) -> str | None:
        async with self._make_client() as client:
            await self._ensure_schema(client)
            result = await client.execute(
                libsql_client.Statement(
                    "SELECT summary_text FROM agent_summaries WHERE session_id = ?",
                    [self.session_id],
                )
            )
            return result.rows[0][0] if result.rows else None

    async def get_items_unsummarized(self) -> tuple[list[TResponseInputItem], int]:
        """Return (items_outside_window_not_yet_summarized, last_id_of_those_items)."""
        async with self._make_client() as client:
            await self._ensure_schema(client)

            # ID up to which we already have a summary
            sum_result = await client.execute(
                libsql_client.Statement(
                    "SELECT summarized_up_to_id FROM agent_summaries WHERE session_id = ?",
                    [self.session_id],
                )
            )
            summarized_up_to_id = int(sum_result.rows[0][0]) if sum_result.rows else 0

            # ID of the oldest message still inside the window
            boundary_result = await client.execute(
                libsql_client.Statement(
                    f"SELECT id FROM {self.messages_table} WHERE session_id = ? "
                    f"ORDER BY id DESC LIMIT 1 OFFSET {SUMMARY_WINDOW}",
                    [self.session_id],
                )
            )
            if not boundary_result.rows:
                return [], 0  # not enough messages to need summarization

            boundary_id = int(boundary_result.rows[0][0])
            if boundary_id <= summarized_up_to_id:
                return [], 0  # already summarized up to the current boundary

            msgs_result = await client.execute(
                libsql_client.Statement(
                    f"SELECT id, message_data FROM {self.messages_table} "
                    f"WHERE session_id = ? AND id > ? AND id <= ? ORDER BY id ASC",
                    [self.session_id, summarized_up_to_id, boundary_id],
                )
            )
            if not msgs_result.rows:
                return [], 0

            items = [json.loads(row[1]) for row in msgs_result.rows]
            last_id = int(msgs_result.rows[-1][0])
            return items, last_id  # type: ignore[return-value]

    async def save_summary(self, summary_text: str, summarized_up_to_id: int) -> None:
        async with self._make_client() as client:
            await self._ensure_schema(client)
            await client.execute(
                libsql_client.Statement(
                    """
                    INSERT INTO agent_summaries (session_id, summary_text, summarized_up_to_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        summary_text = excluded.summary_text,
                        summarized_up_to_id = excluded.summarized_up_to_id,
                        created_at = CURRENT_TIMESTAMP
                    """,
                    [self.session_id, summary_text, summarized_up_to_id],
                )
            )
