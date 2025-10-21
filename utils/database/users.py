# utils/database/users.py
from .connection import get_connection
from typing import Optional, List # 'Optional' wurde hinzugefügt, um den NameError zu beheben

# ------------------------------------------------------------
# User/Leveling Funktionen (NEU HINZUGEFÜGT)
# ------------------------------------------------------------

def log_message_activity(user_id: str) -> None:
    """
    Inkrementiert den 'counter' (XP-Basis) des Users in der 'user'-Tabelle. 
    Fügt den User hinzu, falls er nicht existiert.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Die 'user' Tabelle benötigt 'id', 'counter', 'name' und 'level'.
    # Wir inkrementieren den Counter, der die XP-Basis ist.
    cur.execute("""
        INSERT INTO user (id, counter, name, level) 
        VALUES (%s, 1, 'Unknown', 0)
        ON DUPLICATE KEY UPDATE 
            counter = counter + 1
    """, (user_id,))
    
    conn.commit()
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
    
    # NEU: Logge den aktuellen Wert auch in der max_active_log Tabelle, 
    # falls dieser Teil in Ihrer setup_database existiert.
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
    cur.close()
    conn.close()

def get_max_active(guild_id: str) -> str:
    """
    Ruft den höchsten aufgezeichneten aktiven Benutzerstand ab.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT max_active FROM active_users WHERE guild_id = %s", (guild_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    # Der Rückgabetyp wurde auf str belassen, wie in Ihrer alten Datei
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
    cur.execute("""
        INSERT INTO members (guild_id, max_members)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE max_members = GREATEST(max_members, VALUES(max_members))
    """, (guild_id, count))
    conn.commit()
    cur.close()
    conn.close()

def get_max_members(guild_id: str) -> str:
    """
    Ruft den höchsten aufgezeichneten Mitgliederstand ab.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT max_members FROM members WHERE guild_id = %s", (guild_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    # Der Rückgabetyp wurde auf str belassen, wie in Ihrer alten Datei
    return str(result[0]) if result else "0"