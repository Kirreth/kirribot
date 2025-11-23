from .connection import get_connection
from datetime import datetime, timezone
from typing import Optional, List, Tuple

# ------------------------------------------------------------
# Erinnerungseinstellungen (guild_settings nutzen)
# ------------------------------------------------------------

def set_reminder_channel(guild_id: str, channel_id: str | None) -> None:
    """Speichert den Channel, in dem Bump-Erinnerungen gepostet werden."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO guild_settings (guild_id, bump_reminder_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bump_reminder_channel_id = VALUES(bump_reminder_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_reminder_channel(guild_id: str) -> Optional[int]:
    """Ruft die ID des Channels für Bump-Erinnerungen ab."""
    conn = get_connection()
    cur = conn.cursor()
    result = None
    try:
        cur.execute("""
            SELECT bump_reminder_channel_id FROM guild_settings WHERE guild_id = %s
        """, (guild_id,))
        row = cur.fetchone()
        if row and row[0]:
            result = int(row[0])
    finally:
        cur.close()
        conn.close()
    return result


def set_reminder_status(guild_id: str, status: bool) -> None:
    """Setzt den Reminder-Status für den Server (True/False)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO guild_settings (guild_id, reminder_sent)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE reminder_sent = VALUES(reminder_sent)
        """, (guild_id, int(status)))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_reminder_status(guild_id: str) -> bool:
    """Ruft den Reminder-Status ab."""
    conn = get_connection()
    cur = conn.cursor()
    status = False
    try:
        cur.execute("""
            SELECT reminder_sent FROM guild_settings WHERE guild_id = %s
        """, (guild_id,))
        row = cur.fetchone()
        if row and row[0] is not None:
            status = bool(row[0])
    finally:
        cur.close()
        conn.close()
    return status


# ------------------------------------------------------------
# Letzter Bump Timestamp
# ------------------------------------------------------------

def set_last_bump_time(guild_id: str, timestamp: datetime) -> None:
    """Speichert den UTC-Zeitstempel des letzten Bumps für den Cooldown."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        ts = int(timestamp.timestamp())
        cur.execute("""
            INSERT INTO guild_settings (guild_id, last_bump_timestamp)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE last_bump_timestamp = VALUES(last_bump_timestamp)
        """, (guild_id, ts))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_last_bump_time(guild_id: str) -> Optional[datetime]:
    """Ruft den UTC-Zeitstempel des letzten Bumps ab."""
    conn = get_connection()
    cur = conn.cursor()
    result = None
    try:
        cur.execute("""
            SELECT last_bump_timestamp FROM guild_settings WHERE guild_id = %s
        """, (guild_id,))
        row = cur.fetchone()
        if row and row[0] is not None:
            result = datetime.fromtimestamp(row[0], tz=timezone.utc)
    finally:
        cur.close()
        conn.close()
    return result


# ------------------------------------------------------------
# Alle relevanten Guilds für Bump abrufen
# ------------------------------------------------------------

def get_all_guilds_with_bump_settings() -> List[Tuple[str, Optional[int], Optional[int]]]:
    """
    Ruft Guild-ID, Bump-Reminder-Channel-ID, Reminder-Status und Bumper-Rolle-ID ab.
    Nur Server mit gesetztem Bump-Reminder-Channel werden zurückgegeben.
    """
    conn = get_connection()
    cur = conn.cursor()
    results: List[Tuple[str, Optional[int], Optional[int], bool]] = []
    try:
        cur.execute("""
            SELECT guild_id, bump_reminder_channel_id, bumper_role_id, reminder_sent
            FROM guild_settings
            WHERE bump_reminder_channel_id IS NOT NULL AND bump_reminder_channel_id != ''
        """)
        rows = cur.fetchall()
        for guild_id_str, channel_id_str, role_id_str, status_int in rows:
            channel_id = int(channel_id_str) if channel_id_str else None
            role_id = int(role_id_str) if role_id_str else None
            status = bool(status_int)
            results.append((guild_id_str, channel_id, role_id, status))
    finally:
        cur.close()
        conn.close()
    return results
