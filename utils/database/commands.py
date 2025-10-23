# utils/database/commands.py
from .connection import get_connection
from typing import List, Tuple

# ------------------------------------------------------------
# Commands loggen
# ------------------------------------------------------------

def log_command_usage(command: str, guild_id: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO commands (guild_id, command, uses)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE uses = uses + 1
        """, (guild_id, command))
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Top Commands abrufen
# ------------------------------------------------------------

def get_top_commands(guild_id: str, limit: int) -> List[Tuple[str, int]]:
    conn = get_connection()
    cur = conn.cursor()
    results = []
    try:
        cur.execute("""
            SELECT command, uses FROM commands
            WHERE guild_id = %s
            ORDER BY uses DESC
            LIMIT %s
        """, (guild_id, limit))
        results = cur.fetchall()
    finally:
        cur.close()
        conn.close()
        
    return results