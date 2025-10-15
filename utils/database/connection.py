# utils/database/connection.py
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
        auth_plugin='mysql_native_password' # manchmal nötig für MariaDB
    )


def setup_database():
    """Erstellt alle Tabellen, falls sie nicht existieren"""
    conn = get_connection()
    cursor = conn.cursor()

# ------------------------------------------------------------
# Aktive User (korrigiert: PRIMARY KEY auf max_active)
# ------------------------------------------------------------
    # Achtung: Die Tabelle 'active_users' im Original hatte 'guild_id VARCHAR(20) PRIMARY KEY, max_active INT NOT NULL'
    # und 'max_active' im Log-Bereich hatte einen zusätzlichen 'timestamp'.
    # Hier wird die ursprüngliche 'active_users' beibehalten und die 'max_active' (die einen Zeitstempel hat) angepasst.
    # Da Sie die 'max_active' Tabelle bereits hatten, gehe ich davon aus, diese zu nutzen oder zu korrigieren.

    # Korrektur der ursprünglichen 'active_users' für max_active
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_users (
            guild_id VARCHAR(20) PRIMARY KEY,
            max_active INT NOT NULL
        )
    """)

# ------------------------------------------------------------
# Mitgliederrekord
# ------------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            guild_id VARCHAR(20) PRIMARY KEY,
            max_members INT NOT NULL
        )
    """)


# ------------------------------------------------------------
# Commands loggen
# ------------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            guild_id VARCHAR(20),
            command VARCHAR(50),
            uses INT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, command)
        )
    """)

# ------------------------------------------------------------
# Nachrichten loggen
# ------------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            channel_id VARCHAR(20),
            timestamp BIGINT NOT NULL,
            PRIMARY KEY (guild_id, user_id, channel_id, timestamp)
        )
    """)

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
    
    # NEU: Tabelle für die Gesamtanzahl der Bumps (für /topb)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS total_bumps (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            total_count INT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
    """)
    
    # NEU: Tabelle für den Cooldown-Status pro Server (für /nextbump)
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

# ------------------------------------------------------------
# Geburtstags-Channel
# ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthday_settings (
            guild_id VARCHAR(50) PRIMARY KEY,
            channel_id VARCHAR(50) NOT NULL
        )
    """)


    # Korrigierte Log-Tabelle (die ursprüngliche 'max_active' war schon da)
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