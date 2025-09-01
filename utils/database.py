import sqlite3
import math
from datetime import datetime, timedelta

DB_PATH = "users.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    return conn

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            name TEXT,
            id TEXT PRIMARY KEY,
            counter INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        );
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeouts (
            user_id TEXT,
            guild_id TEXT,
            duration_minutes INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id TEXT,
            guild_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bumps (
            user_id TEXT,
            guild_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()



def berechne_level(counter):
    return int(math.sqrt(counter))

def berechne_level_und_progress(counter):
    level = int(math.sqrt(counter))
    naechstes_level_anfang = level ** 2
    naechstes_level_ende = (level + 1) ** 2
    progress = (counter - naechstes_level_anfang) / (naechstes_level_ende - naechstes_level_anfang)
    progress = max(0.0, min(progress, 1.0))
    return level, progress


def add_warn(user_id, guild_id, reason):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO warns (user_id, guild_id, reason) VALUES (?, ?, ?)", (user_id, guild_id, reason))
    conn.commit()
    conn.close()

def get_warns(user_id, guild_id, within_hours=None):
    conn = get_connection()
    cursor = conn.cursor()
    if within_hours:
        time_limit = datetime.utcnow() - timedelta(hours=within_hours)
        cursor.execute("SELECT * FROM warns WHERE user_id=? AND guild_id=? AND timestamp>=?", (user_id, guild_id, time_limit))
    else:
        cursor.execute("SELECT * FROM warns WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_timeout(user_id, guild_id, duration_minutes, reason):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO timeouts (user_id, guild_id, duration_minutes, reason) VALUES (?, ?, ?, ?)", (user_id, guild_id, duration_minutes, reason))
    conn.commit()
    conn.close()

def get_timeouts(user_id, guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM timeouts WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_ban(user_id, guild_id, reason):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bans (user_id, guild_id, reason) VALUES (?, ?, ?)", (user_id, guild_id, reason))
    conn.commit()
    conn.close()

def get_bans(user_id, guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bans WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    rows = cursor.fetchall()
    conn.close()
    return rows


def log_bump(user_id, guild_id, timestamp=None):
    conn = get_connection()
    cursor = conn.cursor()
    if not timestamp:
        timestamp = datetime.utcnow()
    cursor.execute("INSERT INTO bumps (user_id, guild_id, timestamp) VALUES (?, ?, ?)", (user_id, guild_id, timestamp))
    conn.commit()
    conn.close()

def get_bumps_total(user_id, guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bumps WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_bumps_30d(user_id, guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = datetime.utcnow() - timedelta(days=30)
    cursor.execute("SELECT COUNT(*) FROM bumps WHERE user_id=? AND guild_id=? AND timestamp>=?", (user_id, guild_id, cutoff))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_bump_top(guild_id, days=None, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cursor.execute("""
            SELECT user_id, COUNT(*) as total
            FROM bumps
            WHERE guild_id=? AND timestamp>=?
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """, (guild_id, cutoff, limit))
    else:
        cursor.execute("""
            SELECT user_id, COUNT(*) as total
            FROM bumps
            WHERE guild_id=?
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """, (guild_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows
