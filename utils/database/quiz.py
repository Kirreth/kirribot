# utils/database/quiz.py
from datetime import date
from utils.database import connection as db

def save_quiz_result(user_id: str, guild_id: str, score: int):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_results (user_id, guild_id, score, date_played)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE score = VALUES(score), date_played = VALUES(date_played)
    """, (user_id, guild_id, score, date.today()))
    conn.commit()
    cursor.close()
    conn.close()


def get_last_score(user_id: str, guild_id: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score, date_played FROM quiz_results WHERE user_id = %s AND guild_id = %s", (user_id, guild_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
