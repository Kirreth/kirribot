from .connection import get_connection

def log_command_usage(command: str, guild_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO commands (guild_id, command, uses)
        VALUES (?, ?, 1)
        ON CONFLICT(guild_id, command)
        DO UPDATE SET uses = uses + 1
    """, (guild_id, command))
    conn.commit()
    conn.close()

def get_top_commands(guild_id: str, limit: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT command, uses FROM commands
        WHERE guild_id = ?
        ORDER BY uses DESC
        LIMIT ?
    """, (guild_id, limit))
    results = cur.fetchall()
    conn.close()
    return results
