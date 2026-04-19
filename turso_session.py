from __future__ import annotations

import json

import libsql_client
from agents import SessionSettings
from agents.memory import SessionABC
from agents import TResponseInputItem


def _resolve_limit(limit: int | None, settings: SessionSettings | None) -> int | None:
    if limit is not None:
        return limit
    return settings.limit if settings else None


class TursoSession(SessionABC):
    """Turso-backed session — drop-in replacement for SQLiteSession."""

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
        ])

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        session_limit = _resolve_limit(limit, self.session_settings)
        async with self._make_client() as client:
            await self._ensure_schema(client)
            if session_limit is None:
                result = await client.execute(
                    libsql_client.Statement(
                        f"SELECT message_data FROM {self.messages_table} WHERE session_id = ? ORDER BY id ASC",
                        [self.session_id],
                    )
                )
                rows = result.rows
            else:
                result = await client.execute(
                    libsql_client.Statement(
                        f"SELECT message_data FROM {self.messages_table} WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                        [self.session_id, session_limit],
                    )
                )
                rows = list(reversed(result.rows))

            items = []
            for row in rows:
                try:
                    items.append(json.loads(row[0]))
                except json.JSONDecodeError:
                    continue
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
            ])
