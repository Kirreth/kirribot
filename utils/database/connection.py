# utils/database/connection.py
from pathlib import Path
import sqlite3

# Absoluter Pfad relativ zu dieser Datei
DB_PATH = Path(__file__).parent.parent / "data" / "activity.db"

def get_connection():
    # Vor dem Öffnen sicherstellen, dass der Ordner existiert
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def setup_database():
    conn = get_connection()
    cur = conn.cursor()

    # Tabelle für aktive Nutzer
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_users (
            guild_id TEXT PRIMARY KEY,
            max_active INTEGER
        )
    """)

    # Tabelle für Mitgliederzahlen
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            guild_id TEXT PRIMARY KEY,
            max_members INTEGER
        )
    """)

    # Tabelle für Befehle
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            guild_id TEXT,
            command TEXT,
            uses INTEGER,
            PRIMARY KEY (guild_id, command)
        )
    """)

    # Tabelle für Nachrichten
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            guild_id TEXT,
            user_id TEXT,
            channel_id TEXT,
            timestamp INTEGER
        )
    """)

    conn.commit()
    conn.close()
