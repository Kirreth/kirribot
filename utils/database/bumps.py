# utils/database/bumps.py
from .connection import get_connection
from datetime import datetime, timezone
from typing import Optional, List, Tuple

# ------------------------------------------------------------
# Bumps speichern (Unverändert)
# ------------------------------------------------------------

def log_bump(user_id: str, guild_id: str, timestamp: datetime) -> None:
    conn = get_connection()
    cur = conn.cursor()
    # Wichtig: Speichern Sie den Timestamp immer in UTC (wie in cogs/bumps.py)
    # Python's datetime.timestamp() ist standardmäßig POSIX-Timestamp
    cur.execute("""
        INSERT INTO bumps (guild_id, user_id, timestamp) VALUES (%s, %s, %s)
    """, (guild_id, user_id, int(timestamp.timestamp())))
    conn.commit()
    cur.close()
    conn.close()

# ------------------------------------------------------------
# Gesamtanzahl der Bumps inkrementieren (Unverändert)
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
# Cooldown-Funktionen (NEU)
# ------------------------------------------------------------

def set_last_bump_time(guild_id: str, timestamp: datetime) -> None:
    """Speichert den UTC-Zeitstempel des letzten Bumps für den Cooldown-Check."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Der Zeitstempel wird als POSIX Timestamp gespeichert (int)
    ts = int(timestamp.timestamp())
    
    # UPSERT-Logik für den Server-Status
    cur.execute("""
        INSERT INTO server_status (guild_id, last_bump_timestamp)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) 
        DO UPDATE SET last_bump_timestamp = EXCLUDED.last_bump_timestamp
    """, (guild_id, ts))
    
    conn.commit()
    cur.close()
    conn.close()


def get_last_bump_time(guild_id: str) -> Optional[datetime]:
    """Ruft den UTC-Zeitstempel des letzten Bumps ab."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT last_bump_timestamp FROM server_status WHERE guild_id = %s
    """, (guild_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result is None:
        return None
        
    # Konvertiere den POSIX Timestamp zurück in ein UTC datetime-Objekt
    timestamp_int = result[0]
    # Verwenden Sie timezone.utc, um explizit die Zeitzone zu setzen
    return datetime.fromtimestamp(timestamp_int, tz=timezone.utc)

# ------------------------------------------------------------
# Top Bumper abrufen (Unverändert)
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