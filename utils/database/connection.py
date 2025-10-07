# utils/database/connection.py
from pathlib import Path
import sqlite3

# Absoluter Pfad relativ zu dieser Datei
DB_PATH = Path(__file__).parent.parent / "data" / "activity.db"

def get_connection():
    """Öffnet eine Verbindung zur SQLite-Datenbank und erstellt den Ordner, falls nötig."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def setup_database():
    """Erstellt alle Tabellen mit PRIMARY KEY/UNIQUE Constraints."""
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

    # Tabelle für Befehle (PRIMARY KEY auf guild_id + command)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            guild_id TEXT,
            command TEXT,
            uses INTEGER,
            PRIMARY KEY (guild_id, command)
        )
    """)

    # Tabelle für Nachrichten (PRIMARY KEY auf guild_id + user_id + channel_id + timestamp)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            guild_id TEXT,
            user_id TEXT,
            channel_id TEXT,
            timestamp INTEGER
        )
    """)

    # Tabelle für User-Leveling / Counter
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id TEXT PRIMARY KEY,
            name TEXT,
            counter INTEGER,
            level INTEGER
        )
    """)


    conn.commit()
    conn.close()
