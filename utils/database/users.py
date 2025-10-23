# utils/database/users.py
from .connection import get_connection
from typing import Optional, List, Union

# ------------------------------------------------------------
# User/Leveling Funktionen (KORRIGIERT)
# ------------------------------------------------------------

# 🚩 KORREKTUR: Füge guild_id hinzu, da Leveling pro Server erfolgt
def log_message_activity(user_id: str, guild_id: str) -> None:
    """
    Inkrementiert den 'counter' (XP-Basis) des Users in der 'user'-Tabelle FÜR DIE GEGEBENE GILDE. 
    Fügt den User/Gilden-Eintrag hinzu, falls er nicht existiert.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Die 'user' Tabelle benötigt (id, guild_id, counter, level).
        # Wir inkrementieren den Counter, der die XP-Basis ist.
        # WICHTIG: 'Unknown' für name ist ein Platzhalter, falls dieser Wert im INSERT benötigt wird.
        cur.execute("""
            INSERT INTO user (id, guild_id, counter, level) 
            VALUES (%s, %s, 1, 0)
            ON DUPLICATE KEY UPDATE 
                counter = counter + 1
        """, (user_id, guild_id))
        
        conn.commit()
    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------
# Max Aktiv-Nutzer (active_users Tabelle)
# ------------------------------------------------------------

def set_max_active(guild_id: str, count: int) -> None:
    """
    Setzt den höchsten aufgezeichneten aktiven Benutzerstand (UPSERT).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # NEU: Logge den aktuellen Wert auch in der max_active_log Tabelle
        # Hinweis: Die Verwendung von NOW() hängt von der DB-Implementierung ab (hier MySQL/PostgreSQL).
        cur.execute("""
            INSERT INTO max_active_log (guild_id, max_active, timestamp)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE max_active=VALUES(max_active)
        """, (guild_id, count))
        
        # Ursprüngliche Logik: Höchsten Rekord in active_users speichern
        cur.execute("""
            INSERT INTO active_users (guild_id, max_active)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE max_active = GREATEST(max_active, VALUES(max_active))
        """, (guild_id, count))
        
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_max_active(guild_id: str) -> Union[str, int]:
    """
    Ruft den höchsten aufgezeichneten aktiven Benutzerstand ab.
    """
    conn = get_connection()
    cur = conn.cursor()
    result = None
    try:
        cur.execute("SELECT max_active FROM active_users WHERE guild_id = %s", (guild_id,))
        result = cur.fetchone()
    finally:
        cur.close()
        conn.close()
        
    # Rückgabe als Integer oder String "0" (wie ursprünglich gewünscht)
    return str(result[0]) if result else "0"

# ------------------------------------------------------------
# Max Mitglieder (members Tabelle)
# ------------------------------------------------------------

def set_max_members(guild_id: str, count: int) -> None:
    """
    Setzt den höchsten aufgezeichneten Mitgliederstand (UPSERT).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO members (guild_id, max_members)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE max_members = GREATEST(max_members, VALUES(max_members))
        """, (guild_id, count))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_max_members(guild_id: str) -> Union[str, int]:
    """
    Ruft den höchsten aufgezeichneten Mitgliederstand ab.
    """
    conn = get_connection()
    cur = conn.cursor()
    result = None
    try:
        cur.execute("SELECT max_members FROM members WHERE guild_id = %s", (guild_id,))
        result = cur.fetchone()
    finally:
        cur.close()
        conn.close()
        
    # Rückgabe als Integer oder String "0" (wie ursprünglich gewünscht)
    return str(result[0]) if result else "0"