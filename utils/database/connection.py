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
    """Erstellt alle Tabellen, falls sie nicht existieren"""
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------
    # Aktive User
    # ------------------------------------------------------------
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
    # Nachrichten loggen (messages) – jetzt mit action_count
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            channel_id VARCHAR(20),
            action_count INT NOT NULL DEFAULT 0,
            last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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
