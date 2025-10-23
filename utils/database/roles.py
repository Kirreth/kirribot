# utils/database/roles.py
from .connection import get_connection
from typing import Optional, Any

# ------------------------------------------------------------
# Bumper Rolle setzen
# ------------------------------------------------------------
def set_bumper_role(guild_id: str, role_id: Optional[str]) -> None:
    """
    Speichert die ID der Bumper-Rolle für die gegebene Gilde. 
    Setzt role_id auf None, um die Rolle zu entfernen.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Annahme: Eine Tabelle namens 'guild_settings' oder 'server_config' existiert
        # und speichert Einstellungen pro Gilde.
        cur.execute("""
            INSERT INTO guild_settings (guild_id, bumper_role_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bumper_role_id = VALUES(bumper_role_id)
        """, (guild_id, role_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Bumper Rolle abrufen (optional, aber nützlich)
# ------------------------------------------------------------
def get_bumper_role(guild_id: str) -> Optional[str]:
    """Ruft die gespeicherte Bumper-Rollen-ID ab."""
    conn = get_connection()
    cur = conn.cursor()
    result = None
    try:
        cur.execute(
            "SELECT bumper_role_id FROM guild_settings WHERE guild_id = %s", 
            (guild_id,)
        )
        result = cur.fetchone()
    finally:
        cur.close()
        conn.close()
        
    return str(result[0]) if result and result[0] else None