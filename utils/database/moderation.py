from .connection import get_connection
import time

def add_warn(user_id: str, guild_id: str, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    cur.execute(
        "INSERT INTO warns (user_id, guild_id, reason) VALUES (?, ?, ?)",
        (user_id, guild_id, reason)
    )
    conn.commit()
    conn.close()

def get_warns(user_id: str, guild_id: str, within_hours: int = 24):
    cutoff = int(time.time()) - within_hours * 3600
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT reason, timestamp FROM warns
        WHERE user_id = ? AND guild_id = ? AND timestamp > ?
    """, (user_id, guild_id, cutoff))
    results = cur.fetchall()
    conn.close()
    return results

def add_timeout(user_id: str, guild_id: str, minutes: int, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            user_id TEXT,
            guild_id TEXT,
            minutes INTEGER,
            reason TEXT,
            timestamp INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    cur.execute(
        "INSERT INTO timeouts (user_id, guild_id, minutes, reason) VALUES (?, ?, ?, ?)",
        (user_id, guild_id, minutes, reason)
    )
    conn.commit()
    conn.close()

def add_ban(user_id: str, guild_id: str, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    cur.execute(
        "INSERT INTO bans (user_id, guild_id, reason) VALUES (?, ?, ?)",
        (user_id, guild_id, reason)
    )
    conn.commit()
    conn.close()
