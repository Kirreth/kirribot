# utils/database/bumps.py
from .connection import get_connection
from datetime import datetime
from typing import Optional, List, Tuple

# ------------------------------------------------------------
# Bumps speichern
# ------------------------------------------------------------

def log_bump(user_id: str, guild_id: str, timestamp: datetime) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bumps (guild_id, user_id, timestamp) VALUES (%s, %s, %s)
    """, (guild_id, user_id, int(timestamp.timestamp())))
    conn.commit()
    cur.close()
    conn.close()

# ------------------------------------------------------------
# Gesamtanzahl der Bumps inkrementieren
# ------------------------------------------------------------

def increment_total_bumps(user_id: str, guild_id: str) -> None:
    """Inkrementiert die Gesamtanzahl der Bumps für den Benutzer im Guild."""
    conn = get_connection()
    cur = conn.cursor()
    # UPSERT-Logik: Versuche zu aktualisieren, wenn vorhanden; füge andernfalls ein.
    cur.execute("""
        INSERT INTO total_bumps (guild_id, user_id, total_count)
        VALUES (%s, %s, 1)
        ON CONFLICT (guild_id, user_id) 
        DO UPDATE SET total_count = total_bumps.total_count + 1
    """, (guild_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

# ------------------------------------------------------------
# Top Bumper abrufen
# ------------------------------------------------------------

def get_bump_top(guild_id: str, days: Optional[int] = None, limit: int = 3) -> List[Tuple[str, int]]:
    conn = get_connection()
    cur = conn.cursor()
    
    if days:
        # Monats-Top: Zählt weiterhin aus der 'bumps' Log-Tabelle
        cutoff = int(datetime.utcnow().timestamp()) - days * 86400
        cur.execute("""
            SELECT user_id, COUNT(*) as count FROM bumps
            WHERE guild_id = %s AND timestamp > %s
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT %s
        """, (guild_id, cutoff, limit))
    else:
        # Gesamt-Top: Liest direkt aus der 'total_bumps' Zählertabelle
        cur.execute("""
            SELECT user_id, total_count FROM total_bumps
            WHERE guild_id = %s
            ORDER BY total_count DESC
            LIMIT %s
        """, (guild_id, limit))
        
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results