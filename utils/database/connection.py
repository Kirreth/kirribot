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
    # Bestehende Tabellen bleiben unverändert
    # ------------------------------------------------------------
    # ... hier bleibt dein bestehender Code unverändert ...

    # ------------------------------------------------------------
    # Neue Tabellen für Post-System
    # ------------------------------------------------------------
    # Tabelle für Posts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            guild_id VARCHAR(20) NOT NULL,
            author_id VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            link VARCHAR(255),
            status ENUM('pending','approved','denied') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabelle für Guild-spezifische Post-Channels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_post_channels (
            guild_id VARCHAR(20) PRIMARY KEY,
            checkpost_channel_id VARCHAR(20),
            post_channel_id VARCHAR(20)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Datenbank-Setup abgeschlossen (inklusive Post-System).")
