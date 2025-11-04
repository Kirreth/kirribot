import datetime
from utils.database import connection as db
from typing import Optional, List, Tuple

# ------------------------------------------------------------
# Präfix setzen/abrufen
# ------------------------------------------------------------

def get_prefix(guild_id: str) -> Optional[str]:
    """Ruft das Command-Präfix für den Server ab (Standard: '!')."""
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT prefix FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    
    # Standard-Präfix zurückgeben, falls kein Eintrag gefunden wird
    return result[0] if result and result[0] else '!'

def set_prefix(guild_id: str, prefix: str) -> None:
    """Setzt das Command-Präfix für den Server."""
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
# Sanctions/Mod-Log Channel setzen/abrufen
# ------------------------------------------------------------

def get_sanctions_channel(guild_id: str) -> Optional[str]:
    """Ruft die ID des Channels für Mod-Logs/Sanctions ab."""
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
    """Setzt die ID des Channels für Mod-Logs/Sanctions."""
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
# Birthday Channel setzen/abrufen
# ------------------------------------------------------------

def get_birthday_channel(guild_id: str) -> Optional[str]:
    """Ruft die ID des Channels für Geburtstagsglückwünsche ab."""
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
    """Setzt die ID des Channels für Geburtstagsglückwünsche."""
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
# Bump Channel setzen/abrufen
# ------------------------------------------------------------

def get_bump_reminder_channel(guild_id: str) -> Optional[str]:
    """Ruft die ID des Channels für Bump-Erinnerungen ab."""
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
    """Setzt die ID des Channels für Bump-Erinnerungen."""
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


# ------------------------------------------------------------
# Bumper Rolle setzen/abrufen
# ------------------------------------------------------------

def get_bumper_role(guild_id: str) -> Optional[str]:
    """Ruft die ID der Bumper-Rolle ab."""
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
    """Setzt die ID der Bumper-Rolle."""
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
# Alle Bump-Einstellungen abrufen (für die Hintergrundaufgabe)
# ------------------------------------------------------------
def get_all_bump_settings() -> List[Tuple[str, str, str]]:
    """
    Ruft alle Gilden-Einstellungen ab, die für Bump-Erinnerungen relevant sind,
    einschließlich Channel-ID und Bumper-Rollen-ID.
    
    Format: List[(guild_id, bump_reminder_channel_id, bumper_role_id), ...]
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    result = []
    try:
        # Wir wählen nur Einträge aus, bei denen mindestens ein Reminder-Channel gesetzt ist
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
# Quiz Belohnungsrolle setzen/abrufen
# ------------------------------------------------------------

def get_quiz_reward_role(guild_id: str) -> Optional[str]:
    """Ruft die ID der Quiz-Belohnungsrolle ab."""
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT quiz_reward_role_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    
    return result[0] if result else None

def set_quiz_reward_role(guild_id: str, role_id: str | None) -> None:
    """Setzt die ID der Quiz-Belohnungsrolle."""
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO guild_settings (guild_id, quiz_reward_role_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE quiz_reward_role_id = VALUES(quiz_reward_role_id)
        """, (guild_id, role_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Dynamic Voice Channel setzen/abrufen
# ------------------------------------------------------------

def get_dynamic_voice_channel(guild_id: str) -> Optional[str]:
    """Ruft die ID des 'Join-to-Create' Starter-Channels ab."""
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
    """Setzt die ID des 'Join-to-Create' Starter-Channels."""
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