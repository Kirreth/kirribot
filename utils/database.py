import sqlite3
import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

DB_PATH: str = "users.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    return conn


def setup_database() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            name TEXT,
            id TEXT PRIMARY KEY,
            counter INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            user_id TEXT,
            guild_id TEXT,
            duration_minutes INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bumps (
            user_id TEXT,
            guild_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            guild_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS max_active (
            guild_id TEXT PRIMARY KEY,
            max_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_usage (
            command_name TEXT,
            guild_id TEXT,
            uses INTEGER DEFAULT 0,
            PRIMARY KEY (command_name, guild_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS max_members (
            guild_id TEXT PRIMARY KEY,
            count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def berechne_level(counter: int) -> int:
    return int(math.sqrt(counter))


def berechne_level_und_rest(counter: int) -> tuple[int, int]:
    level = int(counter ** 0.5)
    next_level = level + 1
    needed_for_next = next_level ** 2
    rest = max(needed_for_next - counter, 0)
    return level, rest


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
    return [(str(row[0]), int(row[1])) for row in rows]


def log_message(user_id: str, guild_id: str, timestamp: Optional[datetime] = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    if not timestamp:
        timestamp = datetime.utcnow()
    cursor.execute(
        "INSERT INTO messages (user_id, guild_id, timestamp) VALUES (?, ?, ?)",
        (user_id, guild_id, timestamp)
    )
    conn.commit()
    conn.close()


def get_top_messages(guild_id: str, days: int = 30, limit: int = 3) -> List[Tuple[str, int]]:
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = datetime.utcnow() - timedelta(days=days)
    cursor.execute("""
        SELECT user_id, COUNT(*) as total
        FROM messages
        WHERE guild_id=? AND timestamp>=?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT ?
    """, (guild_id, cutoff, limit))
    rows = cursor.fetchall()
    conn.close()
    return [(str(row[0]), int(row[1])) for row in rows]


def get_max_active(guild_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT max_count FROM max_active WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def set_max_active(guild_id: str, count: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO max_active (guild_id, max_count, timestamp)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(guild_id) DO UPDATE SET
            max_count=excluded.max_count,
            timestamp=CURRENT_TIMESTAMP
    """, (guild_id, count))
    conn.commit()
    conn.close()


def log_command_usage(command_name: str, guild_id: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO command_usage (command_name, guild_id, uses)
        VALUES (?, ?, 1)
        ON CONFLICT(command_name, guild_id) 
        DO UPDATE SET uses = uses + 1;
    """, (command_name, guild_id))
    conn.commit()
    conn.close()


def get_top_commands(guild_id: str, limit: int = 5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT command_name, uses
        FROM command_usage
        WHERE guild_id=?
        ORDER BY uses DESC
        LIMIT ?
    """, (guild_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]


def set_max_members(guild_id: str, count: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM max_members WHERE guild_id=?", (guild_id,))
    result = cursor.fetchone()
    if result is None or count > result[0]:
        cursor.execute("""
            INSERT INTO max_members (guild_id, count, timestamp)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                count=excluded.count,
                timestamp=CURRENT_TIMESTAMP
        """, (guild_id, count))
    conn.commit()
    conn.close()


def get_max_members(guild_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM max_members WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0
