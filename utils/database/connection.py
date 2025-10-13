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
        auth_plugin='mysql_native_password'  # manchmal nötig für MariaDB
    )


def setup_database():
    """Erstellt alle Tabellen, falls sie nicht existieren"""
    conn = get_connection()
    cursor = conn.cursor()

    # aktive Nutzer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_users (
            guild_id VARCHAR(20) PRIMARY KEY,
            max_active INT NOT NULL
        )
    """)

    # Mitgliederzahlen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            guild_id VARCHAR(20) PRIMARY KEY,
            max_members INT NOT NULL
        )
    """)

    # Befehle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            guild_id VARCHAR(20),
            command VARCHAR(50),
            uses INT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, command)
        )
    """)

    # Nachrichten
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            channel_id VARCHAR(20),
            timestamp BIGINT NOT NULL,
            PRIMARY KEY (guild_id, user_id, channel_id, timestamp)
        )
    """)

    # User-Leveling / Counter
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(50),
            counter INT NOT NULL DEFAULT 0,
            level INT NOT NULL DEFAULT 0
        )
    """)

    # Bumps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bumps (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            timestamp BIGINT NOT NULL,
            PRIMARY KEY (guild_id, user_id, timestamp)
        )
    """)

    # Moderation: Warns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            reason VARCHAR(255),
            timestamp BIGINT NOT NULL
        )
    """)

    # Moderation: Timeouts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            duration_minutes INT,
            reason VARCHAR(255),
            timestamp BIGINT NOT NULL
        )
    """)

    # Moderation: Bans
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            guild_id VARCHAR(20),
            user_id VARCHAR(20),
            reason VARCHAR(255),
            timestamp BIGINT NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
