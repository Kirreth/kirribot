# utils/database/messages.py
from .connection import get_connection
import time

def log_channel_activity(channel_id: str, guild_id: str, user_id: str = "system"):
    timestamp = int(time.time())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (guild_id, user_id, channel_id, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (guild_id, user_id, channel_id, timestamp))
    conn.commit()
    cur.close()
    conn.close()

def log_message(guild_id: str, user_id: str, channel_id: str):
    timestamp = int(time.time())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (guild_id, user_id, channel_id, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (guild_id, user_id, channel_id, timestamp))
    conn.commit()
    cur.close()
    conn.close()

def get_top_channels(guild_id: str, days: int = 30, limit: int = 5):
    cutoff = int(time.time()) - (days * 86400)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT channel_id, COUNT(*) as count FROM messages
        WHERE guild_id = %s AND timestamp > %s
        GROUP BY channel_id
        ORDER BY count DESC
        LIMIT %s
    """, (guild_id, cutoff, limit))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def get_top_messages(guild_id: str, days: int = 30, limit: int = 5):
    cutoff = int(time.time()) - (days * 86400)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, COUNT(*) as count FROM messages
        WHERE guild_id = %s AND timestamp > %s AND user_id != 'system'
        GROUP BY user_id
        ORDER BY count DESC
        LIMIT %s
    """, (guild_id, cutoff, limit))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
