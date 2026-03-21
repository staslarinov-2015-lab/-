from __future__ import annotations

import aiosqlite


CREATE_EXPENSES_TABLE = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER,
    user_name TEXT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class ExpenseRepository:
    def __init__(self, db_path: str = "expenses.db") -> None:
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_EXPENSES_TABLE)
            await db.commit()

    async def add_expense(
        self,
        *,
        chat_id: int,
        user_id: int | None,
        user_name: str,
        amount: float,
        category: str,
        description: str,
        created_at: str,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO expenses (
                    chat_id, user_id, user_name, amount, category, description, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, user_name, amount, category, description, created_at),
            )
            await db.commit()

    async def fetch_expenses_between(
        self,
        *,
        chat_id: int,
        start_iso: str,
        end_iso: str,
    ) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, chat_id, user_id, user_name, amount, category, description, created_at
                FROM expenses
                WHERE chat_id = ?
                  AND created_at >= ?
                  AND created_at < ?
                ORDER BY created_at DESC
                """,
                (chat_id, start_iso, end_iso),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
