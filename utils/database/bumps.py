# utils/database/bumps.py
from .connection import get_connection
from datetime import datetime
from typing import Optional, List, Tuple

def log_bump(user_id: str, guild_id: str, timestamp: datetime) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bumps (guild_id, user_id, timestamp) VALUES (%s, %s, %s)
    """, (guild_id, user_id, int(timestamp.timestamp())))
    conn.commit()
    cur.close()
    conn.close()

def get_bump_top(guild_id: str, days: Optional[int] = None, limit: int = 3) -> List[Tuple[str, int]]:
    conn = get_connection()
    cur = conn.cursor()
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
            SELECT user_id, COUNT(*) as count FROM bumps
            WHERE guild_id = %s
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT %s
        """, (guild_id, limit))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
