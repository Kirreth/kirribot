# utils/database/messages.py
from .connection import get_connection
import time

def log_channel_activity(channel_id: str, guild_id: str, user_id: str = "system"):
    """Speichert eine Aktivität in der messages-Tabelle."""
    timestamp = int(time.time())
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO messages (guild_id, user_id, channel_id, timestamp)
            VALUES (?, ?, ?, ?)
        """, (guild_id, user_id, channel_id, timestamp))

def get_top_channels(guild_id: str, days: int = 30, limit: int = 5):
    """Gibt die aktivsten Channels zurück."""
    cutoff = int(time.time()) - (days * 86400)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT channel_id, COUNT(*) as count FROM messages
            WHERE guild_id = ? AND timestamp > ?
            GROUP BY channel_id
            ORDER BY count DESC
            LIMIT ?
        """, (guild_id, cutoff, limit))
        return cur.fetchall()

def log_message(guild_id: str, user_id: str, channel_id: str):
    """Speichert eine normale Nachricht in der messages-Tabelle."""
    timestamp = int(time.time())
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO messages (guild_id, user_id, channel_id, timestamp)
            VALUES (?, ?, ?, ?)
        """, (guild_id, user_id, channel_id, timestamp))

def get_top_messages(guild_id: str, days: int = 30, limit: int = 5):
    """Gibt die aktivsten User nach Nachrichtenanzahl zurück."""
    cutoff = int(time.time()) - (days * 86400)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, COUNT(*) as count FROM messages
            WHERE guild_id = ? AND timestamp > ?
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT ?
        """, (guild_id, cutoff, limit))
        return cur.fetchall()
