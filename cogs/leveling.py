import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union, Optional
from utils.database import connection as db
from utils.database import messages as db_messages
import random
from PIL import Image, ImageDraw, ImageFont
import io
import os
import math

# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------

def get_base_path(*paths: str) -> str:
    """Erstellt einen sicheren Pfad relativ zum Projektverzeichnis."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    return os.path.join(base_dir, *paths)

# ------------------------------------------------------------
# Schriftarten laden
# ------------------------------------------------------------

try:
    FONT_PATH = get_base_path("assets", "fonts", "RobotoMono-VariableFont_wght.ttf")
    font_main = ImageFont.truetype(FONT_PATH, 40)
    font_small = ImageFont.truetype(FONT_PATH, 30)
except Exception as e:
    print(f"⚠️ Fehler beim Laden der Schriftart: {e}")
    font_main = ImageFont.load_default()
    font_small = ImageFont.load_default()

# ------------------------------------------------------------
# Levelberechnung (N²-System)
# ------------------------------------------------------------

def berechne_level(counter: int) -> int:
    """Berechnet das Level anhand der N²-Formel."""
    if counter < 1:
        return 0
    return int(math.sqrt(counter))

def berechne_fortschritt(counter: int, level: int):
    """
    Gibt (progress_percent (0..1), xp_rest:int) zurück.
    Berechnet den Fortschritt und die verbleibenden XP bis zum nächsten Level.
    """
    if level <= 0:
        prev_threshold = 0
    else:
        prev_threshold = level * level

    next_level = level + 1
    next_threshold = next_level * next_level

    xp_in_level = counter - prev_threshold
    xp_needed = next_threshold - prev_threshold

    progress_percent = xp_in_level / xp_needed if xp_needed > 0 else 1.0
    progress_percent = max(0.0, min(1.0, progress_percent))

    xp_rest = max(0, next_threshold - counter)
    return progress_percent, xp_rest

# ------------------------------------------------------------
# Rank Card erstellen
# ------------------------------------------------------------

async def create_rank_card(member: discord.User, counter: int, level: int, rank: int, progress_percent: float, xp_left: int) -> io.BytesIO:
    """Erstellt das Rank-Bild mit farbigem, halbtransparentem Overlay je nach Level."""
    width, height = 800, 200
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

# ------------------------------------------------------------
# Hintergrundbild laden
# ------------------------------------------------------------
    try:
        images_dir = get_base_path("images")
        all_files = [f for f in os.listdir(images_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if all_files:
            bg_file = random.choice(all_files)
            bg_path = os.path.join(images_dir, bg_file)
            bg_img = Image.open(bg_path).resize((width, height)).convert("RGBA")
            img = Image.alpha_composite(img, bg_img)
        else:
            fallback = Image.new("RGBA", (width, height), (10, 10, 10, 255))
            img = Image.alpha_composite(img, fallback)
    except Exception as e:
        print(f"⚠️ Hintergrund konnte nicht geladen werden: {e}")
        fallback = Image.new("RGBA", (width, height), (10, 10, 10, 255))
        img = Image.alpha_composite(img, fallback)

 # ------------------------------------------------------------
# Overlay nach Level
# ------------------------------------------------------------
    if level <= 5:
        overlay_color = (0, 0, 0, 100)          # Dunkel / neutral
    elif level <= 10:
        overlay_color = (0, 80, 180, 120)       # Blau
    elif level <= 20:
        overlay_color = (120, 0, 150, 120)      # Lila
    else:
        overlay_color = (255, 215, 0, 130)      # Gold

    overlay = Image.new("RGBA", (width, height), overlay_color)
    img = Image.alpha_composite(img, overlay)

# ------------------------------------------------------------
# Avatar rund einfügen
# ------------------------------------------------------------
    try:
        avatar_size = (150, 150)
        asset = member.display_avatar.with_format("png").with_size(256)
        data = io.BytesIO(await asset.read())
        avatar_img = Image.open(data).resize(avatar_size).convert("RGBA")

        mask = Image.new("L", avatar_size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size[0], avatar_size[1]), fill=255)
        img.paste(avatar_img, (25, 25), mask)
    except Exception as e:
        print(f"⚠️ Avatar konnte nicht geladen werden: {e}")

# ------------------------------------------------------------
# Text und Fortschritstsbalken
# ------------------------------------------------------------
    draw = ImageDraw.Draw(img)
    fill_color = "#FFFFFF"

    draw.text((200, 30), f"Level: {level}", fill=fill_color, font=font_main)
    draw.text((400, 30), f"Rank: {rank}", fill=fill_color, font=font_main)
    draw.text((600, 30), f"XP: {counter}", fill=fill_color, font=font_main)

# ------------------------------------------------------------
# Fortschrittsbalken
# ------------------------------------------------------------
    bar_x, bar_y = 200, 120
    bar_width = 550
    bar_height = 25

    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(51, 51, 51, 255))
    draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * progress_percent), bar_y + bar_height], fill=(255, 255, 255, 255))

    for i in range(0, bar_width, 15):
        draw.line([(bar_x + i, bar_y), (bar_x + i, bar_y + bar_height)], fill=(17, 17, 17, 255), width=1)

    #draw.text((bar_x, bar_y + 35), f"Noch {xp_left} Nachrichten bis Level {level + 1}", fill=fill_color, font=font_small)

# ------------------------------------------------------------
# Ausgabe vorbereiten
# ------------------------------------------------------------
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf





# ------------------------------------------------------------
# Cog-Klasse für das Levelsystem
# ------------------------------------------------------------

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        uid = str(message.author.id)
        uname = message.author.name
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        db_messages.log_message(guild_id, uid, channel_id)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id=%s", (uid,))
        result = cursor.fetchone()

        counter = 1 if result is None else result[0] + 1
        level = berechne_level(counter)

        if result is None:
            cursor.execute(
                "INSERT INTO user (id, name, counter, level) VALUES (%s, %s, %s, %s)",
                (uid, uname, counter, level),
            )
        else:
            cursor.execute(
                "UPDATE user SET counter=%s, level=%s WHERE id=%s",
                (counter, level, uid),
            )

        conn.commit()
        cursor.close()
        conn.close()

    @commands.hybrid_command(name="rank", description="Zeigt das Profil des Users im Matrix-Style")
    async def rank(self, ctx: Context[commands.Bot], user: Optional[Union[discord.User, discord.Member]] = None):
        """Zeigt das Level-Profil eines Users."""
        user = user or ctx.author
        uid = str(user.id)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id=%s", (uid,))
        result = cursor.fetchone()

        if not result:
            await ctx.send(embed=discord.Embed(
                title=f"{user.name} hat noch keine Nachrichten geschrieben.",
                color=discord.Color.red()
            ))
            cursor.close()
            conn.close()
            return

        counter = result[0]
        level = berechne_level(counter)
        progress_percent, xp_rest = berechne_fortschritt(counter, level)

        # Rang berechnen
        cursor.execute("SELECT COUNT(*) + 1 FROM user WHERE counter > %s", (counter,))
        rank_res = cursor.fetchone()
        rank = rank_res[0] if rank_res else 1

        cursor.close()
        conn.close()

        image_stream = await create_rank_card(user, counter, level, rank, progress_percent, xp_rest)
        await ctx.send(file=discord.File(image_stream, filename=f"rank_card_{user.name}.png"))

# ------------------------------------------------------------
# Cog Setup
# ------------------------------------------------------------

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
