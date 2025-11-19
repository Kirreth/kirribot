import datetime
from utils.database import connection as db
from typing import Optional, List, Tuple

# ------------------------------------------------------------
# Präfix setzen/abrufen
# ------------------------------------------------------------

def get_prefix(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT prefix FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result and result[0] else '!'

def set_prefix(guild_id: str, prefix: str) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, prefix)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE prefix = VALUES(prefix)
        """, (guild_id, prefix))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Sanctions/Mod-Log Channel
# ------------------------------------------------------------

def get_sanctions_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT sanction_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_sanctions_channel(guild_id: str, channel_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, sanction_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE sanction_channel_id = VALUES(sanction_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Birthday Channel
# ------------------------------------------------------------

def get_birthday_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT birthday_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_birthday_channel(guild_id: str, channel_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, birthday_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE birthday_channel_id = VALUES(birthday_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Bump Reminder Channel
# ------------------------------------------------------------

def get_bump_reminder_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT bump_reminder_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_bump_reminder_channel(guild_id: str, channel_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, bump_reminder_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bump_reminder_channel_id = VALUES(bump_reminder_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
def get_all_bump_settings() -> list[tuple[str, str, str]]:
    """
    Ruft alle Gilden-Einstellungen ab, die für Bump-Erinnerungen relevant sind,
    einschließlich Channel-ID und Bumper-Rollen-ID.
    Format: List[(guild_id, bump_reminder_channel_id, bumper_role_id), ...]
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    result = []
    try:
        cursor.execute("""
            SELECT guild_id, bump_reminder_channel_id, bumper_role_id
            FROM guild_settings
            WHERE bump_reminder_channel_id IS NOT NULL AND bump_reminder_channel_id != ''
        """)
        result = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return result

# ------------------------------------------------------------
# Bumper Rolle
# ------------------------------------------------------------

def get_bumper_role(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT bumper_role_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_bumper_role(guild_id: str, role_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, bumper_role_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bumper_role_id = VALUES(bumper_role_id)
        """, (guild_id, role_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Dynamic Voice Channel
# ------------------------------------------------------------

def get_dynamic_voice_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT dynamic_voice_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_dynamic_voice_channel(guild_id: str, channel_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, dynamic_voice_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE dynamic_voice_channel_id = VALUES(dynamic_voice_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Post Channels
# ------------------------------------------------------------

def get_checkpost_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT checkpost_channel_id FROM guild_post_channels WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_checkpost_channel(guild_id: str, channel_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_post_channels (guild_id, checkpost_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE checkpost_channel_id = VALUES(checkpost_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_post_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT post_channel_id FROM guild_post_channels WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return result[0] if result else None

def set_post_channel(guild_id: str, channel_id: str | None) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_post_channels (guild_id, post_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE post_channel_id = VALUES(post_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
