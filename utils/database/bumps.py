# utils/database/bumps.py
from .connection import get_connection
from datetime import datetime, timezone
from typing import Optional, List, Tuple

# ------------------------------------------------------------
# Bumps speichern
# ------------------------------------------------------------

def log_bump(user_id: str, guild_id: str, timestamp: datetime) -> None:
    """Protokolliert jeden einzelnen Bump-Vorgang in der 'bumps' Log-Tabelle."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO bumps (guild_id, user_id, timestamp) 
            VALUES (%s, %s, %s)
        """, (guild_id, user_id, int(timestamp.timestamp())))
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Gesamtanzahl der Bumps inkrementieren
# ------------------------------------------------------------

def increment_total_bumps(user_id: str, guild_id: str) -> None:
    """Inkrementiert die Gesamtanzahl der Bumps für den Benutzer im Guild (MySQL-korrigiert)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO bump_totals (guild_id, user_id, total_count)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE 
                total_count = total_count + 1
        """, (guild_id, user_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Cooldown-Funktionen
# ------------------------------------------------------------

def set_last_bump_time(guild_id: str, timestamp: datetime) -> None:
    """Speichert den UTC-Zeitstempel des letzten Bumps für den Cooldown-Check (MySQL-korrigiert)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        ts = int(timestamp.timestamp())
        
        cur.execute("""
            INSERT INTO server_status (guild_id, last_bump_timestamp)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
                last_bump_timestamp = VALUES(last_bump_timestamp)
        """, (guild_id, ts))
        
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_last_bump_time(guild_id: str) -> Optional[datetime]:
    """Ruft den UTC-Zeitstempel des letzten Bumps ab."""
    conn = get_connection()
    cur = conn.cursor()
    result = None
    
    try:
        cur.execute("""
            SELECT last_bump_timestamp FROM server_status WHERE guild_id = %s
        """, (guild_id,))
        
        result = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if result is None or result[0] is None:
        return None
        
    timestamp_int = result[0]
    return datetime.fromtimestamp(timestamp_int, tz=timezone.utc)

# ------------------------------------------------------------
# Top Bumper abrufen
# ------------------------------------------------------------

def get_bump_top(guild_id: str, days: Optional[int] = None, limit: int = 3) -> List[Tuple[str, int]]:
    """Ruft die Top-Bumper ab, entweder insgesamt oder über einen bestimmten Zeitraum."""
    conn = get_connection()
    cur = conn.cursor()
    results = []
    
    try:
        if days:
            cutoff = int(datetime.utcnow().timestamp()) - days * 86400
            cur.execute("""
                SELECT user_id, COUNT(*) as count FROM bumps
                WHERE guild_id = %s AND timestamp > %s
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT %s
            """, (guild_id, cutoff, limit))
        else:
            cur.execute("""
                SELECT user_id, total_count FROM bump_totals
                WHERE guild_id = %s
                ORDER BY total_count DESC
                LIMIT %s
            """, (guild_id, limit))
            
        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
        
    return results