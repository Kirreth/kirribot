# utils/database/users.py
from .connection import get_connection

# ------------------------------------------------------------
# Maximale aktive Nutzer setzen
# ------------------------------------------------------------

def set_max_active(guild_id: str, count: int):
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

# ------------------------------------------------------------
# Maximale Nutzer setzen
# ------------------------------------------------------------

def set_max_members(guild_id: str, count: int):
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

# ------------------------------------------------------------
# Maximale aktive Nutzer abrufen
# ------------------------------------------------------------

def get_max_members(guild_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT max_members FROM members WHERE guild_id = %s", (guild_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None
