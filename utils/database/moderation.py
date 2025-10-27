# utils/database/moderation.py
from .connection import get_connection
import time
from typing import List, Tuple, Any

# ------------------------------------------------------------
# User-Warns hinzufügen
# ------------------------------------------------------------

def add_warn(user_id: str, guild_id: str, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO warns (user_id, guild_id, reason, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (user_id, guild_id, reason, int(time.time())))
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# User-Warns abrufen
# ------------------------------------------------------------

def get_warns(user_id: str, guild_id: str, within_hours: int = 24) -> List[Tuple[Any, ...]]:
    cutoff = int(time.time()) - within_hours * 3600
    conn = get_connection()
    cur = conn.cursor()
    results = []
    try:
        cur.execute("""
        SELECT timestamp, reason FROM warns
        WHERE user_id = %s AND guild_id = %s AND timestamp > %s
        """, (user_id, guild_id, cutoff))

        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return results


# ------------------------------------------------------------
# User-Warns löschen
# ------------------------------------------------------------
def clear_warns(user_id: str, guild_id: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM warns WHERE user_id = %s AND guild_id = %s
        """, (user_id, guild_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------
# User-Timeouts hinzufügen
# ------------------------------------------------------------

def add_timeout(user_id: str, guild_id: str, minutes: int, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO timeouts (user_id, guild_id, duration_minutes, reason, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, guild_id, minutes, reason, int(time.time())))
        conn.commit()
    finally:
        cur.close()
        conn.close()

#-------------
# User-Timeouts abrufen
#-------------
def get_timeouts(user_id: str, guild_id: str) -> List[Tuple[Any, ...]]:
    conn = get_connection()
    cur = conn.cursor()
    results = []
    try:
        cur.execute("""
        SELECT timestamp, duration_minutes, reason FROM timeouts
        WHERE user_id = %s AND guild_id = %s
        """, (user_id, guild_id))

        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return results

# ------------------------------------------------------------
# User Bann hinzufügen
# ------------------------------------------------------------

def add_ban(user_id: str, guild_id: str, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO bans (user_id, guild_id, reason, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (user_id, guild_id, reason, int(time.time())))
        conn.commit()
    finally:
        cur.close()
        conn.close()

#-------------
# User Bann abrufen
#-------------
def get_bans(user_id: str, guild_id: str) -> List[Tuple[Any, ...]]:
    conn = get_connection()
    cur = conn.cursor()
    results = []
    try:
        # Ruft alle Bans ab
        cur.execute("""
        SELECT timestamp, reason FROM bans
        WHERE user_id = %s AND guild_id = %s
        """, (user_id, guild_id))

        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return results

# ------------------------------------------------------------
# Sanktionen-Kanal setzen  
# ------------------------------------------------------------


def set_sanctions_channel(guild_id: str, channel_id: str | None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO server_status (guild_id, sanctions_channel)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                sanctions_channel = VALUES(sanctions_channel)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()