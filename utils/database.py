import sqlite3
import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

DB_PATH: str = "users.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Zugriff per Spaltenname
    return conn


def setup_database() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # --- User ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            name TEXT,
            id TEXT PRIMARY KEY,
            counter INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        );
    """)

    # --- Warnungen ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Timeouts ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            user_id TEXT,
            guild_id TEXT,
            duration_minutes INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Bans ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Bumps ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bumps (
            user_id TEXT,
            guild_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


# --- Level-Logik ---
def berechne_level(counter: int) -> int:
    return int(math.sqrt(counter))


def berechne_level_und_progress(counter: int) -> Tuple[int, float]:
    level: int = int(math.sqrt(counter))
    naechstes_level_anfang: int = level ** 2
    naechstes_level_ende: int = (level + 1) ** 2
    progress: float = (counter - naechstes_level_anfang) / (naechstes_level_ende - naechstes_level_anfang)
    progress = max(0.0, min(progress, 1.0))
    return level, progress


# --- Warns ---
def add_warn(user_id: str, guild_id: str, reason: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO warns (user_id, guild_id, reason) VALUES (?, ?, ?)",
        (user_id, guild_id, reason)
    )
    conn.commit()
    conn.close()


def get_warns(user_id: str, guild_id: str, within_hours: Optional[int] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    if within_hours:
        time_limit = datetime.utcnow() - timedelta(hours=within_hours)
        cursor.execute(
            "SELECT * FROM warns WHERE user_id=? AND guild_id=? AND timestamp>=?",
            (user_id, guild_id, time_limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM warns WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


# --- Timeouts ---
def add_timeout(user_id: str, guild_id: str, duration_minutes: int, reason: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO timeouts (user_id, guild_id, duration_minutes, reason) VALUES (?, ?, ?, ?)",
        (user_id, guild_id, duration_minutes, reason)
    )
    conn.commit()
    conn.close()


def get_timeouts(user_id: str, guild_id: str) -> List[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM timeouts WHERE user_id=? AND guild_id=?",
        (user_id, guild_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# --- Bans ---
def add_ban(user_id: str, guild_id: str, reason: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bans (user_id, guild_id, reason) VALUES (?, ?, ?)",
        (user_id, guild_id, reason)
    )
    conn.commit()
    conn.close()


def get_bans(user_id: str, guild_id: str) -> List[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM bans WHERE user_id=? AND guild_id=?",
        (user_id, guild_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# --- Bumps ---
def log_bump(user_id: str, guild_id: str, timestamp: Optional[datetime] = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    if not timestamp:
        timestamp = datetime.utcnow()
    cursor.execute(
        "INSERT INTO bumps (user_id, guild_id, timestamp) VALUES (?, ?, ?)",
        (user_id, guild_id, timestamp)
    )
    conn.commit()
    conn.close()


def get_bumps_total(user_id: str, guild_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM bumps WHERE user_id=? AND guild_id=?",
        (user_id, guild_id)
    )
    count: int = cursor.fetchone()[0]
    conn.close()
    return count


def get_bumps_30d(user_id: str, guild_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cutoff: datetime = datetime.utcnow() - timedelta(days=30)
    cursor.execute(
        "SELECT COUNT(*) FROM bumps WHERE user_id=? AND guild_id=? AND timestamp>=?",
        (user_id, guild_id, cutoff)
    )
    count: int = cursor.fetchone()[0]
    conn.close()
    return count


def get_bump_top(guild_id: str, days: Optional[int] = None, limit: int = 10) -> List[Tuple[str, int]]:
    conn = get_connection()
    cursor = conn.cursor()
    if days:
        cutoff: datetime = datetime.utcnow() - timedelta(days=days)
        cursor.execute("""
            SELECT user_id, COUNT(*) as total
            FROM bumps
            WHERE guild_id=? AND timestamp>=?
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """, (guild_id, cutoff, limit))
    else:
        cursor.execute("""
            SELECT user_id, COUNT(*) as total
            FROM bumps
            WHERE guild_id=?
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """, (guild_id, limit))
    rows = cursor.fetchall()
    conn.close()
    # sqlite3.Row -> Tuple[str, int]
    return [(str(row[0]), int(row[1])) for row in rows]

