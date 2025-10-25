# utils/database/messages.py
from .connection import get_connection
from typing import List, Tuple

# ------------------------------------------------------------
# Aktivität loggen (UPSERT-Ansatz)
# ------------------------------------------------------------

def log_channel_activity(channel_id: str, guild_id: str, user_id: str) -> None:
    """
    Protokolliert eine Kanalaktivität. Erhöht den Zähler für (guild_id, channel_id, user_id),
    wenn der Eintrag existiert (UPSERT), andernfalls wird ein neuer Eintrag erstellt.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO messages (guild_id, user_id, channel_id, action_count)
            VALUES (%s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE 
                action_count = action_count + 1,
                last_action = CURRENT_TIMESTAMP
        """, (guild_id, user_id, channel_id))
        
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Nachrichten loggen
# ------------------------------------------------------------

def log_message(guild_id: str, user_id: str, channel_id: str) -> None:
    """
    Loggt eine reguläre Nachricht. Ruft log_channel_activity mit der richtigen Parameterreihenfolge auf.
    """
    log_channel_activity(channel_id, guild_id, user_id)


# ------------------------------------------------------------
# Top Channels (Basierend auf action_count)
# ------------------------------------------------------------

def get_top_channels(guild_id: str, limit: int = 5) -> List[Tuple[str, int]]:
    """
    Gibt die aktivsten Channels basierend auf der Gesamtanzahl der Aktionen (action_count) zurück.
    """
    conn = get_connection()
    cur = conn.cursor()
    results = []
    
    try:
        cur.execute("""
            SELECT channel_id, SUM(action_count) as total_count FROM messages
            WHERE guild_id = %s
            GROUP BY channel_id
            ORDER BY total_count DESC
            LIMIT %s
        """, (guild_id, limit))
        
        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
        
    return results

# ------------------------------------------------------------
# Top Chatter/User (Basierend auf action_count)
# ------------------------------------------------------------

def get_top_messages(guild_id: str, limit: int = 5) -> List[Tuple[str, int]]:
    """
    Gibt die Top-User basierend auf ihrer action_count zurück (ohne Systemaktivität).
    """
    conn = get_connection()
    cur = conn.cursor()
    results = []

    try:
        cur.execute("""
            SELECT user_id, SUM(action_count) as total_count FROM messages
            WHERE guild_id = %s AND user_id != 'system'
            GROUP BY user_id
            ORDER BY total_count DESC
            LIMIT %s
        """, (guild_id, limit))
        
        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
        
    return results