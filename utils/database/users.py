# utils/database/users.py
from .connection import get_connection

# ------------------------------------------------------------
# Max Aktiv-Nutzer (active_users Tabelle)
# ------------------------------------------------------------

def set_max_active(guild_id: str, count: int) -> None:
    """
    Setzt den höchsten aufgezeichneten aktiven Benutzerstand (UPSERT).
    """
    conn = get_connection()
    cur = conn.cursor()
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
    # KORREKTUR: Abfrage der Spalte max_active aus der Tabelle active_users.
    cur.execute("SELECT max_active FROM active_users WHERE guild_id = %s", (guild_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
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
    Diese Funktion behebt den 'AttributeError' in activitytracker.py.
    """
    conn = get_connection()
    cur = conn.cursor()
    # KORREKTUR: Abfrage der Spalte max_members aus der Tabelle members.
    cur.execute("SELECT max_members FROM members WHERE guild_id = %s", (guild_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return str(result[0]) if result else "0"