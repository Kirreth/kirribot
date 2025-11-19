# utils/database/posts.py
from .connection import get_connection

# -----------------------------
# Post-Funktionen
# -----------------------------

def add_post(guild_id: str, author_id: str, name: str, content: str, link: str) -> int:
    """Fügt einen neuen Post ein und gibt die post_id zurück."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (guild_id, author_id, name, content, link)
        VALUES (%s, %s, %s, %s, %s)
    """, (guild_id, author_id, name, content, link))
    conn.commit()
    post_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return post_id

def get_post(post_id: int) -> dict | None:
    """Gibt einen Post anhand der ID zurück."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM posts WHERE post_id = %s", (post_id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()
    return post

def set_post_status(post_id: int, status: str) -> None:
    """Ändert den Status eines Posts ('pending', 'approved', 'denied')."""
    if status not in ("pending", "approved", "denied"):
        raise ValueError("Status muss 'pending', 'approved' oder 'denied' sein.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET status = %s WHERE post_id = %s", (status, post_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_pending_posts(guild_id: str) -> list[dict]:
    """Gibt alle pending-Posts für eine Guild zurück."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM posts WHERE guild_id = %s AND status = 'pending'", (guild_id,))
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return posts

# -----------------------------
# Guild-Post-Channels
# -----------------------------

def set_check_channel(guild_id: str, channel_id: str | None) -> None:
    """Setzt den Channel für Checkposts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guild_post_channels (guild_id, checkpost_channel_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE checkpost_channel_id = VALUES(checkpost_channel_id)
    """, (guild_id, channel_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_check_channel(guild_id: str) -> str | None:
    """Gibt die Checkpost-Channel-ID zurück."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT checkpost_channel_id FROM guild_post_channels WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result and result[0] else None

def set_post_channel(guild_id: str, channel_id: str | None) -> None:
    """Setzt den Channel für genehmigte Posts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guild_post_channels (guild_id, post_channel_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE post_channel_id = VALUES(post_channel_id)
    """, (guild_id, channel_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_post_channel(guild_id: str) -> str | None:
    """Gibt die Post-Channel-ID zurück."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT post_channel_id FROM guild_post_channels WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result and result[0] else None
