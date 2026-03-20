# utils/database/counter.py
from .connection import get_connection

def add_new_counter(guild_id: str, word: str) -> bool:
    """
    Registriert ein neues Wort für einen Server in der Datenbank.
    Gibt True zurück, wenn es neu angelegt wurde, False wenn es schon existiert.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Prüfen, ob das Wort für diese Guild bereits registriert ist
        cursor.execute(
            "SELECT word FROM word_counters WHERE guild_id = %s AND word = %s", 
            (guild_id, word)
        )
        if cursor.fetchone():
            return False
            
        cursor.execute(
            "INSERT INTO word_counters (guild_id, word, count) VALUES (%s, %s, 0)", 
            (guild_id, word)
        )
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

def increment_all_matches(guild_id: str, message_content: str):
    """
    Prüft den Inhalt einer Nachricht auf alle für die Guild registrierten Wörter.
    Erhöht den Zähler für jedes gefundene Wort.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Alle registrierten Wörter für diesen Server abrufen
        cursor.execute("SELECT word FROM word_counters WHERE guild_id = %s", (guild_id,))
        registered_words = [row[0] for row in cursor.fetchall()]
        
        content_lower = message_content.lower()
        
        for word in registered_words:
            # Wir prüfen, ob das Wort im Text vorkommt (Case-Insensitive)
            if word.lower() in content_lower:
                cursor.execute(
                    "UPDATE word_counters SET count = count + 1 WHERE guild_id = %s AND word = %s",
                    (guild_id, word)
                )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_counter_stats(guild_id: str) -> list:
    """
    Holt alle Wort-Counter einer Guild aus der Datenbank, 
    sortiert nach der Häufigkeit (Absteigend).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT word, count FROM word_counters WHERE guild_id = %s ORDER BY count DESC", 
            (guild_id,)
        )
        return cursor.fetchall() # Gibt Liste von Tuples zurück: [('moin', 12), ('test', 5)]
    finally:
        cursor.close()
        conn.close()

def delete_counter(guild_id: str, word: str) -> bool:
    """
    Löscht einen Wort-Counter komplett aus der Datenbank.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM word_counters WHERE guild_id = %s AND word = %s", 
            (guild_id, word)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def reset_counter(guild_id: str, word: str) -> bool:
    """
    Setzt den Zähler eines Wortes zurück auf 0, ohne das Wort zu löschen.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE word_counters SET count = 0 WHERE guild_id = %s AND word = %s", 
            (guild_id, word)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()