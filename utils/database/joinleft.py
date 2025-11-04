import mysql.connector
from utils.database.connection import get_connection


def set_welcome_channel(guild_id: str, channel_id: str | None):
    """
    Speichert oder entfernt den Welcome-Channel für einen Server in guild_settings.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO guild_settings (guild_id, welcome_channel_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE welcome_channel_id = VALUES(welcome_channel_id)
    """, (guild_id, channel_id))

    conn.commit()
    cursor.close()
    conn.close()


def get_welcome_channel(guild_id: str) -> str | None:
    """
    Gibt die gespeicherte Welcome-Channel-ID aus guild_settings zurück, falls vorhanden.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT welcome_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result[0] if result and result[0] else None
