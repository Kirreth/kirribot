# utils/database/custom_commands.py
from utils.database import connection as db
from typing import Optional, Dict, Any, List

# ------------------------------------------------------------
# Custom Command hinzufügen oder aktualisieren
# ------------------------------------------------------------
def add_command(guild_id: str, command_name: str, response: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO custom_commands (guild_id, command_name, response)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE response = VALUES(response)
        """, (guild_id, command_name, response))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Einzelnen Custom Command abrufen
# ------------------------------------------------------------
def get_command(guild_id: str, command_name: str) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("""
            SELECT command_name, response
            FROM custom_commands
            WHERE guild_id = %s AND command_name = %s
        """, (guild_id, command_name))
        row = cursor.fetchone()
        if row:
            # Key-Namen an Template & Bot anpassen
            result = {"name": row[0], "response": row[1]}
    finally:
        cursor.close()
        conn.close()
    return result

# ------------------------------------------------------------
# Custom Command entfernen
# ------------------------------------------------------------
def remove_command(guild_id: str, command_name: str) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM custom_commands
            WHERE guild_id = %s AND command_name = %s
        """, (guild_id, command_name))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------
# Alle Commands eines Servers abrufen
# ------------------------------------------------------------
def get_all_commands(guild_id: str) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("""
            SELECT command_name, response
            FROM custom_commands
            WHERE guild_id = %s
        """, (guild_id,))
        rows = cursor.fetchall()
        for row in rows:
            # Key-Namen an Template & Bot anpassen
            results.append({"name": row[0], "response": row[1]})
    finally:
        cursor.close()
        conn.close()
    return results
