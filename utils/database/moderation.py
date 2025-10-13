# utils/database/moderation.py
from .connection import get_connection
import time

def add_warn(user_id: str, guild_id: str, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO warns (user_id, guild_id, reason, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (user_id, guild_id, reason, int(time.time())))
    conn.commit()
    cur.close()
    conn.close()

def get_warns(user_id: str, guild_id: str, within_hours: int = 24):
    cutoff = int(time.time()) - within_hours * 3600
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT reason, timestamp FROM warns
        WHERE user_id = %s AND guild_id = %s AND timestamp > %s
    """, (user_id, guild_id, cutoff))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def add_timeout(user_id: str, guild_id: str, minutes: int, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO timeouts (user_id, guild_id, duration_minutes, reason, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, guild_id, minutes, reason, int(time.time())))
    conn.commit()
    cur.close()
    conn.close()

def add_ban(user_id: str, guild_id: str, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bans (user_id, guild_id, reason, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (user_id, guild_id, reason, int(time.time())))
    conn.commit()
    cur.close()
    conn.close()
