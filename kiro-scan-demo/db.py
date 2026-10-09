# db.py — Database helpers
# All queries use parameterized placeholders (?). String interpolation into SQL
# is never used, which eliminates SQL injection in this module.

import sqlite3
import logging
import config

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row factory enabled."""
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row   # rows accessible by column name
    return conn


def init_db() -> None:
    """Create tables if they do not already exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title   TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.commit()


def get_user_by_username(username: str):
    """
    Look up a user by username.

    FIX (was CRITICAL — SQL Injection): replaced string concatenation with a
    parameterized query. The username value is never interpolated into SQL text.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return row


def search_notes(user_id: int, keyword: str):
    """
    Return notes for user_id whose title contains keyword.

    FIX (was HIGH — SQL Injection): replaced string concatenation with a
    parameterized LIKE query. Both user_id and keyword are bound parameters.
    """
    pattern = f"%{keyword}%"
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE user_id = ? AND title LIKE ?",
            (user_id, pattern),
        ).fetchall()
    return rows


def get_notes_for_user(user_id: int):
    """Return all notes belonging to user_id."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return rows


def add_note(user_id: int, title: str, content: str) -> None:
    """Insert a new note for user_id."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, content),
        )
        conn.commit()


def add_user(username: str, password_hash: str) -> None:
    """Insert a new user with an already-hashed password."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()


def get_all_users():
    """
    Return all users for the admin panel.
    Password column is intentionally excluded — callers never need raw hashes.
    """
    with get_connection() as conn:
        rows = conn.execute("SELECT id, username FROM users").fetchall()
    return rows
