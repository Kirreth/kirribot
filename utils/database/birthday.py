# utils/database/birthday.py
import datetime
from utils.database import connection as db
from typing import Optional, List, Tuple, Any


# ------------------------------------------------------------
# Geburtstag speichern oder aktualisieren
# ------------------------------------------------------------
def set_birthday(user_id: str, guild_id: str, birthday: datetime.date):
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO birthdays (user_id, guild_id, birthday)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE birthday = VALUES(birthday)
        """, (user_id, guild_id, birthday))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# Geburtstag abrufen
# ------------------------------------------------------------
def get_birthday(user_id: str, guild_id: str) -> Optional[datetime.date]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute(
            "SELECT birthday FROM birthdays WHERE user_id = %s AND guild_id = %s", 
            (user_id, guild_id)
        )
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
        
    return result[0] if result else None


# ------------------------------------------------------------
# Channel für Geburtstagsnachrichten setzen
# ------------------------------------------------------------
def set_birthday_channel(guild_id: str, channel_id: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO birthday_settings (guild_id, channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# Channel-ID abrufen
# ------------------------------------------------------------
def get_birthday_channel(guild_id: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT channel_id FROM birthday_settings WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
        
    return result[0] if result else None


# ------------------------------------------------------------
# Alle heutigen Geburtstage abrufen (mit Altersberechnung)
# ------------------------------------------------------------
def get_today_birthdays() -> List[Tuple[Any, ...]]:
    today = datetime.date.today()
    conn = db.get_connection()
    cursor = conn.cursor()
    result = []
    try:
        cursor.execute("""
            SELECT user_id, guild_id, birthday
            FROM birthdays
            WHERE MONTH(birthday) = %s AND DAY(birthday) = %s
              AND (last_congratulated IS NULL OR last_congratulated < %s)
        """, (today.month, today.day, today))
        result = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        
    return result


# ------------------------------------------------------------
# Speichern, dass jemand bereits gratuliert wurde
# ------------------------------------------------------------
def mark_congratulated(user_id: str, guild_id: str):
    today = datetime.date.today()
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE birthdays SET last_congratulated = %s WHERE user_id = %s AND guild_id = %s", 
            (today, user_id, guild_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# Geburtstag entfernen
# ------------------------------------------------------------
def remove_birthday(user_id: str, guild_id: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM birthdays WHERE user_id = %s AND guild_id = %s", (user_id, guild_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()