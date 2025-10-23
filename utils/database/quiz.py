# utils/database/quiz.py
from datetime import date
from utils.database import connection as db
from typing import Optional, Tuple, Any

# ------------------------------------------------------------
# Quiz-Ergebnis speichern oder aktualisieren
# ------------------------------------------------------------

def save_quiz_result(user_id: str, guild_id: str, score: int):
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO quiz_results (user_id, guild_id, score, date_played)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE score = VALUES(score), date_played = VALUES(date_played)
        """, (user_id, guild_id, score, date.today()))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# Letztes Ergebnis abrufen
# ------------------------------------------------------------

def get_last_score(user_id: str, guild_id: str) -> Optional[Tuple[Any, ...]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute("SELECT score, date_played FROM quiz_results WHERE user_id = %s AND guild_id = %s", (user_id, guild_id))
        result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
        
    return result