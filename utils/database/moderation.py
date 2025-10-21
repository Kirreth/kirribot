# utils/database/moderation.py
from .connection import get_connection
import time
# ------------------------------------------------------------
# User-Warns hinzufügen
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# User-Warns abrufen
# ------------------------------------------------------------

def get_warns(user_id: str, guild_id: str, within_hours: int = 24):
    cutoff = int(time.time()) - within_hours * 3600
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT timestamp, reason FROM warns
    WHERE user_id = %s AND guild_id = %s AND timestamp > %s
    """, (user_id, guild_id, cutoff))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# ------------------------------------------------------------
# User-Warns löschen
# ------------------------------------------------------------
def clear_warns(user_id: str, guild_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM warns WHERE user_id = %s AND guild_id = %s
    """, (user_id, guild_id))
    conn.commit()
    cur.close()
    conn.close()


# ------------------------------------------------------------
# User-Timeouts hinzufügen
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# User Bann hinzufügen
# ------------------------------------------------------------

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
