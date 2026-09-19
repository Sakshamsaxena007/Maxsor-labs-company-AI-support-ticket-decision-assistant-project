import json
import sqlite3
from typing import Optional

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    message             TEXT NOT NULL,
    order_value_inr     REAL,
    days_since_delivery INTEGER,
    days_since_dispatch INTEGER,
    product_type        TEXT,
    opened_status       TEXT,
    order_status        TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decisions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL UNIQUE,
    action     TEXT NOT NULL,
    reason     TEXT NOT NULL,
    confidence REAL NOT NULL,
    sources    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


# ---------- Users ----------

def create_user(email: str, password_hash: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.lower().strip(), password_hash),
        )
        return cur.lastrowid


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


# ---------- Tickets ----------

def create_ticket(user_id: int, ticket: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO tickets
               (user_id, message, order_value_inr, days_since_delivery,
                days_since_dispatch, product_type, opened_status, order_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                ticket["message"],
                ticket.get("order_value_inr"),
                ticket.get("days_since_delivery"),
                ticket.get("days_since_dispatch"),
                ticket.get("product_type"),
                ticket.get("opened_status"),
                ticket.get("order_status"),
            ),
        )
        return cur.lastrowid


def save_decision(ticket_id: int, decision: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO decisions (ticket_id, action, reason, confidence, sources)
               VALUES (?, ?, ?, ?, ?)""",
            (
                ticket_id,
                decision["action"],
                decision["reason"],
                float(decision["confidence"]),
                json.dumps(decision["sources"]),
            ),
        )


def _row_to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    if item.get("sources"):
        item["sources"] = json.loads(item["sources"])
    return item


def list_tickets_for_user(user_id: int) -> list[dict]:
    """Only ever returns rows owned by user_id - this IS the authorization rule."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT t.*, d.action, d.reason, d.confidence, d.sources
               FROM tickets t LEFT JOIN decisions d ON d.ticket_id = t.id
               WHERE t.user_id = ?
               ORDER BY t.id DESC""",
            (user_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def get_ticket_for_user(ticket_id: int, user_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT t.*, d.action, d.reason, d.confidence, d.sources
               FROM tickets t LEFT JOIN decisions d ON d.ticket_id = t.id
               WHERE t.id = ? AND t.user_id = ?""",
            (ticket_id, user_id),
        ).fetchone()
        return _row_to_dict(row) if row else None


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
