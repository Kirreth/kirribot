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
    """Erstellt einen sicheren Pfad relativ zum Projekt-Wurzelverzeichnis."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    return os.path.join(base_dir, *paths)

# ------------------------------------------------------------
# Schriftarten laden
# ------------------------------------------------------------

try:
    FONT_PATH = get_base_path("assets", "fonts", "RobotoMono-VariableFont_wght.ttf")
    font_main = ImageFont.truetype(FONT_PATH, 40)
    font_small = ImageFont.truetype(FONT_PATH, 25) 
    font_tiny = ImageFont.truetype(FONT_PATH, 20)
    # NEUE SCHRIFTART für den Namen
    font_name = ImageFont.truetype(FONT_PATH, 30) 
except Exception as e:
    print(f"⚠️ Fehler beim Laden der Schriftart: {e}")
    font_main = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_tiny = ImageFont.load_default()
    font_name = ImageFont.load_default()

# ------------------------------------------------------------
# Levelberechnung (Unverändert)
# ------------------------------------------------------------

def berechne_level(counter: int) -> int:
    if counter < 1:
        return 0
    return int(math.sqrt(counter))

def berechne_fortschritt(counter: int, level: int):
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
    
    return progress_percent, xp_in_level, xp_needed

# ------------------------------------------------------------
# Rank Card erstellen
# ------------------------------------------------------------

async def create_rank_card(member: discord.User, counter: int, level: int, rank: int, progress_percent: float, xp_current_in_level: int, xp_needed_for_level_up: int) -> io.BytesIO:
    """Erstellt das Rank-Bild mit Benutzername, weißer Schrift/Balken und leichtem Overlay."""
    width, height = 800, 200
    fallback_color = (30, 30, 30, 255) 
    
    img = Image.new("RGBA", (width, height), fallback_color) 
    
    # 🎨 Farbeinstellungen: IMMER WEISS
    fill_color = "#FFFFFF" 
    progress_color = (255, 255, 255, 255) 
    
    # ------------------------------------------------------------
    # Hintergrundbild laden (Unverändert)
    # ------------------------------------------------------------
    try:
        images_dir = get_base_path("images") 
        valid_extensions = [".png", ".jpg", ".jpeg"]
        image_number = random.randint(1, 10)
        
        found_path = None
        for ext in valid_extensions:
            temp_path = os.path.join(images_dir, f"background{image_number}{ext}")
            if os.path.exists(temp_path):
                found_path = temp_path
                break
        
        if found_path:
            bg_img = Image.open(found_path).resize((width, height)).convert("RGBA")
            img = Image.alpha_composite(img, bg_img)

    except Exception:
        pass 
        
    draw = ImageDraw.Draw(img) 

    # ------------------------------------------------------------
    # 🌑 KONTRAST-OVERLAY HINZUFÜGEN (Alpha 100/255) 🌑
    # ------------------------------------------------------------
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 100))
    img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img) 
    
    # ------------------------------------------------------------
    # Avatar rund einfügen (Unverändert)
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
        
        draw.ellipse((20, 20, 175, 175), outline=(255, 255, 255, 255), width=5)

    except Exception as e:
        print(f"⚠️ Avatar konnte nicht geladen werden: {e}")

    # ------------------------------------------------------------
    # BENUTZERNAME HINZUFÜGEN (Neu)
    # ------------------------------------------------------------
    name_text = member.display_name
    
    # Text-Bounding Box ermitteln, um es rechtsbündig zur rechten Kante zu zentrieren
    # (200 ist die Start-X-Koordinate nach dem Avatar)
    name_x_start = 200
    name_x_end = width - 10 # 790
    
    # Berechnung der Textbreite
    bbox_name = draw.textbbox((0, 0), name_text, font=font_name)
    text_w_name = bbox_name[2] - bbox_name[0]
    
    # Text zentrieren im rechten Bereich
    name_x = name_x_start + ((name_x_end - name_x_start) - text_w_name) // 2
    
    # Platzierung des Namens
    name_y = 5 
    draw.text((name_x, name_y), name_text, fill=fill_color, font=font_name)
    
    # ------------------------------------------------------------
    # Text und Fortschrittsbalken (Koordinaten angepasst)
    # ------------------------------------------------------------
    
    # Level und Rank Positionierung (y-Koordinate von 20 auf 35 verschoben)
    draw.text((200, 35), f"Level: {level}", fill=fill_color, font=font_main)
    draw.text((480, 35), f"Rank: {rank}", fill=fill_color, font=font_main)
    
    # ------------------------------------------------------------
    # Fortschrittsbalken (y-Koordinate von 90 auf 105 verschoben)
    # ------------------------------------------------------------
    bar_x, bar_y = 200, 105
    bar_width = 580 
    bar_height = 25
    
    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(51, 51, 51, 255))
    draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * progress_percent), bar_y + bar_height], fill=progress_color)

    for i in range(0, bar_width, 15):
        draw.line([(bar_x + i, bar_y), (bar_x + i, bar_y + bar_height)], fill=(17, 17, 17, 255), width=1)

    # ------------------------------------------------------------
    # XP-Text (UNTER DEM BALKEN) (y-Koordinate angepasst)
    # ------------------------------------------------------------
    xp_text_total = f"XP: {counter}"
    xp_text_progress = f"{xp_current_in_level}/{xp_needed_for_level_up} XP bis Level {level + 1}"
    
    # 1. Text: Gesamt-XP (linksbündig)
    draw.text((bar_x, bar_y + bar_height + 5), xp_text_total, fill=fill_color, font=font_small)

    # 2. Text: Fortschritt-XP (rechts daneben)
    bbox_total = draw.textbbox((0, 0), xp_text_total, font=font_small)
    text_w_total = bbox_total[2] - bbox_total[0]
    
    start_x_progress = bar_x + text_w_total + 20 

    draw.text((start_x_progress, bar_y + bar_height + 5), xp_text_progress, fill=progress_color, font=font_small)
    
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

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter, level FROM user WHERE id=%s", (uid,))
        result = cursor.fetchone()

        old_level = 0
        if result is None:
            counter = 1
        else:
            counter = result[0] + 1
            old_level = result[1]

        new_level = berechne_level(counter)

        if result is None:
            cursor.execute(
                "INSERT INTO user (id, name, counter, level) VALUES (%s, %s, %s, %s)",
                (uid, uname, counter, new_level),
            )
        else:
            cursor.execute(
                "UPDATE user SET counter=%s, level=%s WHERE id=%s",
                (counter, new_level, uid),
            )

        conn.commit()
        cursor.close()
        conn.close()

        if new_level > old_level:
            try:
                await message.add_reaction("➕")
            except Exception as e:
                print(f"⚠️ Konnte Reaktion nicht hinzufügen: {e}")

# ------------------------------------------------------------
# Rank Befehl
# ------------------------------------------------------------

    @commands.hybrid_command(name="rank", description="Zeigt das Level-Profil eines Users an")
    async def rank(self, ctx: Context[commands.Bot], user: Optional[Union[discord.User, discord.Member]] = None):
        """Zeigt das Level-Profil eines Users."""
        await ctx.defer()
        user = user or ctx.author
        uid = str(user.id)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id=%s", (uid,))
        result = cursor.fetchone()

        if not result:
            await ctx.send(embed=discord.Embed(
                title=f"{user.display_name} hat noch keine Nachrichten geschrieben.",
                color=discord.Color.red()
            ))
            cursor.close()
            conn.close()
            return

        counter = result[0]
        level = berechne_level(counter)
        progress_percent, xp_current_in_level, xp_needed_for_level_up = berechne_fortschritt(counter, level)

# ------------------------------------------------------------
#  Rang berechnen 
# ------------------------------------------------------------
        cursor.execute("SELECT COUNT(*) + 1 FROM user WHERE counter > %s", (counter,))
        rank_res = cursor.fetchone()
        rank = rank_res[0] if rank_res else 1

        cursor.close()
        conn.close()

        image_stream = await create_rank_card(user, counter, level, rank, progress_percent, xp_current_in_level, xp_needed_for_level_up)
        await ctx.send(file=discord.File(image_stream, filename=f"rank_card_{user.name}.png"))

# ------------------------------------------------------------
# Cog Setup 
# ------------------------------------------------------------

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))