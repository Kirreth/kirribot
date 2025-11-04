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


def get_connection():
    """Gibt eine MySQL/MariaDB-Verbindung zurück"""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        auth_plugin='mysql_native_password'
    )


def setup_database():
    """Erstellt alle Tabellen, falls sie nicht existieren, und führt Migrationen durch."""
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------
    # Servereinstellungen (Setup)
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id VARCHAR(20) PRIMARY KEY,
            sanction_channel_id VARCHAR(20),
            birthday_channel_id VARCHAR(20),
            prefix VARCHAR(5) NOT NULL DEFAULT '/',
            dynamic_voice_channel_id VARCHAR(20)
        )
    """)

    # ------------------------------------------------------------
    # Migration für dynamic_voice_channel_id
    # ------------------------------------------------------------
    cursor.execute("SHOW COLUMNS FROM guild_settings LIKE 'dynamic_voice_channel_id'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN dynamic_voice_channel_id VARCHAR(20) AFTER prefix")
            print("✅ Migration: Spalte 'dynamic_voice_channel_id' zur guild_settings hinzugefügt.")
        except Error as e:
            print(f"WARNUNG: Spalte dynamic_voice_channel_id konnte nicht hinzugefügt werden: {e}")

    # ------------------------------------------------------------
    # Nachrichten loggen (messages) - Korrektur der Spalten und UNIQUE KEY
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            channel_id VARCHAR(20)
        )
    """)
    
    
    cursor.execute("SHOW COLUMNS FROM messages LIKE 'action_count'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN action_count INT NOT NULL DEFAULT 0 AFTER channel_id")
        except Error as e:
            print(f"WARNUNG: action_count konnte nicht hinzugefügt werden: {e}")

    cursor.execute("SHOW COLUMNS FROM messages LIKE 'last_action'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER action_count")
        except Error as e:
            print(f"WARNUNG: last_action konnte nicht hinzugefügt werden: {e}")
            
    try:
        cursor.execute("ALTER TABLE messages ADD UNIQUE KEY unique_activity (guild_id, user_id, channel_id)")
    except Error as e:
        if 'Duplicate entry' in str(e):
            print(f"WARNUNG: Unique Index konnte aufgrund bestehender Duplikate nicht hinzugefügt werden. Bitte bereinigen Sie die messages Tabelle. Fehler: {e}")
        elif 'already exists' in str(e):
            pass 
        else:
            print(f"WARNUNG: Index konnte nicht hinzugefügt werden: {e}")

    # ------------------------------------------------------------
    # Levelsystem (user) - MIGRATION DES PRIMARY KEY
    # ------------------------------------------------------------

    cursor.execute("SHOW COLUMNS FROM user LIKE 'guild_id'")
    if cursor.fetchone() is None:
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN guild_id VARCHAR(20) AFTER id")
            print(f"INFO: Fülle user-Tabelle mit alter Server-ID: {EXISTING_GUILD_ID}")
            cursor.execute(f"UPDATE user SET guild_id = '{EXISTING_GUILD_ID}' WHERE guild_id IS NULL OR guild_id = ''")
            conn.commit()

            try:
                cursor.execute("ALTER TABLE user DROP PRIMARY KEY")
            except Error as e:
                if 'Can\'t DROP PRIMARY' not in str(e):
                     print(f"WARNUNG beim Löschen des alten PK in user-Tabelle: {e}")
            
            cursor.execute("ALTER TABLE user ADD PRIMARY KEY (guild_id, id)")
            print("✅ Levelsystem (user-Tabelle) erfolgreich auf Multi-Server migriert.")

        except Error as e:
            print(f"❌ FATALER FEHLER bei der user-Tabelle Migration: {e}")
            
    
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

    # ------------------------------------------------------------
    # Bumper loggen (total_bumps ist bereits korrekt)
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
    
    -- Definiert den Primary Key und den Unique Key, den MySQL für ODKU benötigt.
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
    # Moderation: Warns, Timeouts, Bans
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
    # Geburtstage (birthdays)
    # ------------------------------------------------------------
    
    cursor.execute("SHOW COLUMNS FROM birthdays LIKE 'guild_id'")
    if cursor.fetchone() is not None:
         cursor.execute("SHOW KEYS FROM birthdays WHERE Key_name = 'PRIMARY'")
         keys = cursor.fetchall()
         
         if len(keys) == 1 and keys[0][4] == 'user_id':
             try:
                print(f"INFO: Fülle birthdays-Tabelle mit alter Server-ID: {EXISTING_GUILD_ID}")
                cursor.execute(f"UPDATE birthdays SET guild_id = '{EXISTING_GUILD_ID}' WHERE guild_id IS NULL OR guild_id = ''")
                conn.commit()

                cursor.execute("ALTER TABLE birthdays DROP PRIMARY KEY")
                
                cursor.execute("ALTER TABLE birthdays ADD PRIMARY KEY (user_id, guild_id)")
                print("✅ Geburtstags-Tabelle erfolgreich auf Multi-Server migriert.")
             except Error as e:
                print(f"❌ FATALER FEHLER bei der birthdays-Tabelle Migration: {e}")


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
    # Max Active Log (Bereits korrekt)
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
    # IT-Quiz Ergebnisse (Bereits korrekt)
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