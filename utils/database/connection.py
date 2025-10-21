import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "activity_db")


def get_connection():
    """Gibt eine MySQL/MariaDB-Verbindung zurück"""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        auth_plugin='mysql_native_password'  # manchmal nötig für MariaDB
    )


def setup_database():
    """Erstellt alle Tabellen, falls sie nicht existieren, und fügt fehlende Spalten/Indizes hinzu"""
    conn = get_connection()
    cursor = conn.cursor()

    # ... (Alle anderen Tabellen bleiben unverändert) ...

    # ------------------------------------------------------------
    # Nachrichten loggen (messages)
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            channel_id VARCHAR(20)
        )
    """)
    
    # ⚠️ REPARATUR BLOCK: Fügt fehlende Spalten und den notwendigen UNIQUE INDEX hinzu ⚠️
    
    # 1. Prüfen, ob Spalte 'action_count' existiert, sonst hinzufügen
    cursor.execute("SHOW COLUMNS FROM messages LIKE 'action_count'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN action_count INT NOT NULL DEFAULT 0 AFTER channel_id")
        except Error as e:
            print(f"WARNUNG: action_count konnte nicht hinzugefügt werden: {e}")

    # 2. Prüfen, ob Spalte 'last_action' existiert, sonst hinzufügen
    cursor.execute("SHOW COLUMNS FROM messages LIKE 'last_action'")
    if cursor.fetchone() is None:
        try:
            # Stellt sicher, dass der Zeitstempel automatisch gesetzt wird
            cursor.execute("ALTER TABLE messages ADD COLUMN last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER action_count")
        except Error as e:
            print(f"WARNUNG: last_action konnte nicht hinzugefügt werden: {e}")
            
    # 3. Den fehlenden UNIQUE KEY hinzufügen, der für ON DUPLICATE KEY UPDATE benötigt wird
    # Dies ist die LÖSUNG für den "Field doesn't have a default value" Fehler in messages.py
    try:
        # Versucht, einen Unique Index hinzuzufügen, falls er fehlt.
        # Wichtig: MySQL/MariaDB erlaubt das Hinzufügen eines UNIQUE KEY nur, 
        # wenn die Kombination (guild_id, user_id, channel_id) bisher keine Duplikate enthält.
        # Da Ihre Logik darauf basiert, dass jede Kombination nur einmal existiert (mit Zähler),
        # sollte das funktionieren.
        cursor.execute("ALTER TABLE messages ADD UNIQUE KEY unique_activity (guild_id, user_id, channel_id)")
    except Error as e:
        # Ignoriert den Fehler, falls der Index bereits existiert oder Duplikate vorhanden sind.
        # Wenn der Fehler besagt, dass Duplikate existieren, müssten diese vorher manuell bereinigt werden.
        if 'Duplicate entry' in str(e):
             print(f"WARNUNG: Unique Index konnte aufgrund bestehender Duplikate nicht hinzugefügt werden. Bitte bereinigen Sie die messages Tabelle. Fehler: {e}")
        elif 'already exists' in str(e):
             # Index existiert bereits, alles ist gut
             pass 
        else:
             print(f"WARNUNG: Index konnte nicht hinzugefügt werden: {e}")

    # ... (Alle anderen Tabellen bleiben unverändert) ...
    # (Ich lasse den Rest der setup_database Funktion hier weg, da Sie die komplette Datei 
    # nur aus Platzgründen nicht posten mussten, aber die Korrektur nur hier liegt.)

    # ------------------------------------------------------------
    # Levelsystem
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(50),
            counter INT NOT NULL DEFAULT 0,
            level INT NOT NULL DEFAULT 0
        )
    """)

    # ------------------------------------------------------------
    # Bumper loggen
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bumps (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            timestamp BIGINT NOT NULL,
            PRIMARY KEY (guild_id, user_id, timestamp)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS total_bumps (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            total_count INT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_status (
            guild_id VARCHAR(20) PRIMARY KEY,
            last_bump_timestamp BIGINT
        )
    """)

    # ------------------------------------------------------------
    # Moderation: Warns
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            reason VARCHAR(255),
            timestamp BIGINT NOT NULL
        )
    """)

    # ------------------------------------------------------------
    # Moderation: Timeouts
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            duration_minutes INT,
            reason VARCHAR(255),
            timestamp BIGINT NOT NULL
        )
    """)

    # ------------------------------------------------------------
    # Moderation: Bans
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            reason VARCHAR(255),
            timestamp BIGINT NOT NULL
        )
    """)

    # ------------------------------------------------------------
    # Geburtstage
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthdays (
            user_id VARCHAR(50) PRIMARY KEY,
            guild_id VARCHAR(50),
            birthday DATE NOT NULL,
            last_congratulated DATE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthday_settings (
            guild_id VARCHAR(50) PRIMARY KEY,
            channel_id VARCHAR(50) NOT NULL
        )
    """)

    # ------------------------------------------------------------
    # Max Active Log
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS max_active_log (
            guild_id VARCHAR(20),
            max_active INT,
            timestamp DATETIME,
            PRIMARY KEY (guild_id, timestamp)
        )
    """)

    # ------------------------------------------------------------
    # IT-Quiz Ergebnisse
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            user_id VARCHAR(50),
            guild_id VARCHAR(50),
            score INT NOT NULL,
            date_played DATE NOT NULL,
            PRIMARY KEY (user_id, guild_id)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()