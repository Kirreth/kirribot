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
# Cooldown-Funktionen (Nutzen weiterhin 'server_status' für Cooldown-Zeiten)
# ------------------------------------------------------------

def set_last_bump_time(guild_id: str, timestamp: datetime) -> None:
    """Speichert den UTC-Zeitstempel des letzten Bumps für den Cooldown-Check."""
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

def set_notified_status(guild_id: str, status: bool) -> None:
    """Speichert den Benachrichtigungsstatus (True/False)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Wir nutzen 'reminder_sent' wie in Ihrem Code und Datenbankauszug gezeigt
        cur.execute("""
            INSERT INTO server_status (guild_id, reminder_sent)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE reminder_sent = VALUES(reminder_sent)
        """, (guild_id, int(status)))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_notified_status(guild_id: str) -> bool:
    """Ruft den Benachrichtigungsstatus für einen Server ab."""
    conn = get_connection()
    cur = conn.cursor()
    result = False
    try:
        cur.execute("""
            SELECT reminder_sent FROM server_status WHERE guild_id = %s
        """, (guild_id,))
        row = cur.fetchone()
        
        if row and row[0] is not None:
            result = bool(row[0])
            
    finally:
        cur.close()
        conn.close()
        
    return result

def clear_notified_status(guild_id: str) -> bool:
    """Setzt den Benachrichtigungsstatus für einen Server zurück."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE server_status SET reminder_sent = 0 WHERE guild_id = %s
        """, (guild_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


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

# ------------------------------------------------------------
# Erinnerungseinstellungen (Nutzen nun 'guild_settings' Tabelle)
# ------------------------------------------------------------

def set_reminder_channel(guild_id: str, channel_id: str | None) -> None:
    """Speichert den Channel, in dem Bump-Erinnerungen gepostet werden (nutzt guild_settings)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Nutzung der korrekten Tabelle/Spalte: guild_settings / bump_reminder_channel_id
        cur.execute("""
            INSERT INTO guild_settings (guild_id, bump_reminder_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bump_reminder_channel_id = VALUES(bump_reminder_channel_id)
        """, (guild_id, channel_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_reminder_channel(guild_id: str) -> Optional[int]:
    """Ruft die ID des Channels für Bump-Erinnerungen ab (nutzt guild_settings)."""
    conn = get_connection()
    cur = conn.cursor()
    result = None
    try:
        # Nutzung der korrekten Tabelle/Spalte: guild_settings / bump_reminder_channel_id
        cur.execute("""
            SELECT bump_reminder_channel_id FROM guild_settings WHERE guild_id = %s
        """, (guild_id,))
        row = cur.fetchone()
        if row and row[0]:
            result = int(row[0])
    finally:
        cur.close()
        conn.close()
    return result


# In utils/database/bumps.py ersetzen Sie diese Funktion:

def get_all_guild_settings_with_roles() -> List[Tuple[str, Optional[int], Optional[int]]]:
    """
    Ruft Guild-ID, Reminder-Channel-ID (aus server_status) und Bumper-Rolle-ID (aus guild_settings) ab.
    Die Abfrage stellt sicher, dass NUR Server zurückgegeben werden, die einen Reminder-Channel gesetzt haben.
    """
    conn = get_connection()
    cur = conn.cursor()
    results: List[Tuple[str, Optional[int], Optional[int]]] = []
    try:
        # Führt einen LEFT JOIN durch. Wir wählen die Channel-ID aus server_status.reminder_channel.
        cur.execute("""
            SELECT
                ss.guild_id,
                ss.reminder_channel,  -- HOLT DIE CHANNEL-ID VON server_status
                gs.bumper_role_id
            FROM server_status ss
            LEFT JOIN guild_settings gs ON ss.guild_id = gs.guild_id
            WHERE ss.reminder_channel IS NOT NULL
        """)
        rows = cur.fetchall()
        for guild_id_str, channel_id_str, role_id_str in rows:
            # WICHTIG: Die gespeicherte ID wird zu Integer konvertiert
            channel_id = int(channel_id_str) if channel_id_str else None
            role_id = int(role_id_str) if role_id_str else None
            
            # Format: (guild_id, reminder_channel_id, bumper_role_id)
            results.append((guild_id_str, channel_id, role_id)) 
    finally:
        cur.close()
        conn.close()
        
    return results