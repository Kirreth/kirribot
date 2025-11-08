import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "activity_db")
EXISTING_GUILD_ID = os.getenv("EXISTING_GUILD_ID")

# ------------------------------------------------------------
# Verbindung zur Datenbank
# ------------------------------------------------------------
def get_connection():
    """Gibt eine MySQL/MariaDB-Verbindung zurück"""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        auth_plugin="mysql_native_password"
    )

# ------------------------------------------------------------
# Setup & Migration der Tabellen
# ------------------------------------------------------------
def setup_database():
    """Erstellt alle Tabellen, falls sie nicht existieren, und führt Migrationen durch."""
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------
    # guild_settings (Servereinstellungen)
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id VARCHAR(20) PRIMARY KEY,
            sanction_channel_id VARCHAR(20),
            birthday_channel_id VARCHAR(20),
            prefix VARCHAR(5) NOT NULL DEFAULT '/',
            dynamic_voice_channel_id VARCHAR(20),
            welcome_channel_id VARCHAR(20)
        )
    """)

    # Migration: dynamic_voice_channel_id
    cursor.execute("SHOW COLUMNS FROM guild_settings LIKE 'dynamic_voice_channel_id'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN dynamic_voice_channel_id VARCHAR(20) AFTER prefix")
            print("✅ Migration: 'dynamic_voice_channel_id' hinzugefügt.")
        except Error as e:
            print(f"WARNUNG: dynamic_voice_channel_id konnte nicht hinzugefügt werden: {e}")

    # Migration: welcome_channel_id
    cursor.execute("SHOW COLUMNS FROM guild_settings LIKE 'welcome_channel_id'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN welcome_channel_id VARCHAR(20) AFTER birthday_channel_id")
            print("✅ Migration: 'welcome_channel_id' hinzugefügt.")
        except Error as e:
            print(f"WARNUNG: welcome_channel_id konnte nicht hinzugefügt werden: {e}")

    # ------------------------------------------------------------
    # messages
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            channel_id VARCHAR(20)
        )
    """)

    # Migration: action_count
    cursor.execute("SHOW COLUMNS FROM messages LIKE 'action_count'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN action_count INT NOT NULL DEFAULT 0 AFTER channel_id")
        except Error as e:
            print(f"WARNUNG: action_count konnte nicht hinzugefügt werden: {e}")

    # Migration: last_action
    cursor.execute("SHOW COLUMNS FROM messages LIKE 'last_action'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("""
                ALTER TABLE messages
                ADD COLUMN last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP AFTER action_count
            """)
        except Error as e:
            print(f"WARNUNG: last_action konnte nicht hinzugefügt werden: {e}")

    # Unique Index
    try:
        cursor.execute("ALTER TABLE messages ADD UNIQUE KEY unique_activity (guild_id, user_id, channel_id)")
    except Error as e:
        if "Duplicate" in str(e) or "exists" in str(e):
            pass
        else:
            print(f"WARNUNG: Index konnte nicht hinzugefügt werden: {e}")

    # ------------------------------------------------------------
    # user (Levelsystem)
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            guild_id VARCHAR(20) NOT NULL,
            id VARCHAR(20),
            name VARCHAR(50),
            counter INT NOT NULL DEFAULT 0,
            level INT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, id)
        )
    """)

    # Migration für user.guild_id (Multi-Server)
    cursor.execute("SHOW COLUMNS FROM user LIKE 'guild_id'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN guild_id VARCHAR(20) AFTER id")
            print("INFO: Fülle user-Tabelle mit alter Server-ID ...")
            cursor.execute(f"UPDATE user SET guild_id = '{EXISTING_GUILD_ID}' WHERE guild_id IS NULL OR guild_id = ''")
            conn.commit()

            cursor.execute("ALTER TABLE user DROP PRIMARY KEY")
            cursor.execute("ALTER TABLE user ADD PRIMARY KEY (guild_id, id)")
            print("✅ user-Tabelle erfolgreich migriert (Multi-Server).")
        except Error as e:
            print(f"❌ Fehler bei user-Migration: {e}")

    # ------------------------------------------------------------
    # bumps / bump_totals / server_status
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
        CREATE TABLE IF NOT EXISTS bump_totals (
            guild_id VARCHAR(20) NOT NULL,
            user_id VARCHAR(20) NOT NULL,
            total_count INT DEFAULT 1,
            last_bump_time DATETIME,
            notified_status BOOLEAN DEFAULT FALSE,
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
    # Moderation: Warns / Timeouts / Bans
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
    # birthdays / birthday_settings
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthdays (
            user_id VARCHAR(50),
            guild_id VARCHAR(50),
            birthday DATE NOT NULL,
            last_congratulated DATE,
            PRIMARY KEY (user_id, guild_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthday_settings (
            guild_id VARCHAR(50) PRIMARY KEY,
            channel_id VARCHAR(50) NOT NULL
        )
    """)

    # ------------------------------------------------------------
    # max_active_log
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
    # quiz_results
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


    # ------------------------------------------------------------
    # Dashboard User Token
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_users (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            discord_id VARCHAR(30) NOT NULL UNIQUE,
            username VARCHAR(100),
            avatar_url VARCHAR(255),
            access_token TEXT,
            refresh_token TEXT,
            token_expires DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    #------------------------------------------------------------
    # Custom Commands
    #------------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_commands (
            guild_id VARCHAR(20) NOT NULL,
            command_name VARCHAR(50) NOT NULL,
            response TEXT NOT NULL,
            PRIMARY KEY (guild_id, command_name)
        )
    """)


    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Datenbank-Setup abgeschlossen.")