# utils/database/roles.py
from .connection import get_connection
from typing import Optional, Any, List, Tuple

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
# Bumper Rolle abrufen
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

# ------------------------------------------------------------
# NEU: Alle Server-Einstellungen für die Erinnerungs-Task abrufen
# ------------------------------------------------------------
def get_all_guild_settings() -> List[Tuple[str, str, str]]:
    """
    Ruft alle Guild-IDs, Bumper-Rollen-IDs und den Bump-Kanal für alle 
    Server ab, auf denen beides konfiguriert ist.

    Rückgabe-Format: List[Tuple[guild_id, bumper_role_id, bump_reminder_channel_id]]
    """
    conn = get_connection()
    cur = conn.cursor()
    results: List[Tuple[str, str, str]] = []
    
    # ACHTUNG: Das Feld 'bump_reminder_channel_id' MUSS in Ihrer 'guild_settings'-Tabelle existieren!
    query = """
    SELECT 
        guild_id, 
        bumper_role_id, 
        bump_reminder_channel_id 
    FROM 
        guild_settings 
    WHERE 
        bumper_role_id IS NOT NULL AND bump_reminder_channel_id IS NOT NULL
    """
    
    try:
        cur.execute(query)
        # Type-Cast zur Klarheit. Die DB gibt Strings oder None zurück.
        raw_results = cur.fetchall()
        for row in raw_results:
            # Wir stellen sicher, dass alle drei Werte vorhanden sind (durch WHERE-Klausel)
            if row[0] and row[1] and row[2]:
                 results.append((str(row[0]), str(row[1]), str(row[2])))
    except Exception as e:
        # Fügen Sie hier ein geeignetes Log hinzu, falls ein Logger vorhanden ist
        print(f"Fehler beim Abrufen aller Guild-Einstellungen: {e}")
        return []
    finally:
        cur.close()
        conn.close()
        
    return results