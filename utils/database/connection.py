from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent / "data" / "activity.db"

def get_connection():
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
            timestamp INTEGER,
            PRIMARY KEY (guild_id, user_id, channel_id, timestamp)
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

    # Tabelle für Bumps
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bumps (
            guild_id TEXT,
            user_id TEXT,
            timestamp TEXT,
            PRIMARY KEY (guild_id, user_id, timestamp)
        )
    """)

    # Tabelle für Moderation: Warns / Timeouts / Bans
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            guild_id TEXT,
            user_id TEXT,
            reason TEXT,
            timestamp TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            guild_id TEXT,
            user_id TEXT,
            duration_minutes INTEGER,
            reason TEXT,
            timestamp TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            guild_id TEXT,
            user_id TEXT,
            reason TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()
