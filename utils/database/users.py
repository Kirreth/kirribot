# utils/database/users.py
from .connection import get_connection

def set_max_active(guild_id: str, count: int):
    """Setzt die maximale Anzahl aktiver Nutzer pro Guild."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO active_users (guild_id, max_active)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET max_active = MAX(max_active, excluded.max_active)
        """, (guild_id, count))

def set_max_members(guild_id: str, count: int):
    """Setzt die maximale Anzahl Mitglieder pro Guild."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO members (guild_id, max_members)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET max_members = MAX(max_members, excluded.max_members)
        """, (guild_id, count))

def get_max_members(guild_id: str):
    """Liefert die maximale Mitgliederanzahl einer Guild zurück, falls vorhanden."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT max_members FROM members WHERE guild_id = ?", (guild_id,))
        result = cur.fetchone()
    return result[0] if result else None
