# utils/database/bumps.py
from .connection import get_connection
from datetime import datetime
from typing import Optional, List, Tuple

def log_bump(user_id: str, guild_id: str, timestamp: datetime) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bumps (guild_id, user_id, timestamp) VALUES (?, ?, ?)",
        (guild_id, user_id, timestamp.isoformat())
    )
    conn.commit()
    conn.close()

def get_bump_top(guild_id: str, days: Optional[int] = None, limit: int = 3) -> List[Tuple[str, int]]:
    conn = get_connection()
    cur = conn.cursor()

    if days:
        cutoff = datetime.utcnow().timestamp() - days * 86400
        cur.execute("""
            SELECT user_id, COUNT(*) as count FROM bumps
            WHERE guild_id = ? AND strftime('%s', timestamp) > ?
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT ?
        """, (guild_id, int(cutoff), limit))
    else:
        cur.execute("""
            SELECT user_id, COUNT(*) as count FROM bumps
            WHERE guild_id = ?
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT ?
        """, (guild_id, limit))

    results = cur.fetchall()
    conn.close()
    return results
