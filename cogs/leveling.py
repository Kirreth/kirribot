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
# Levelberechnung
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
    # Hintergrundbild laden
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
        
        draw.ellipse((20, 20, 175, 175), outline=(255, 255, 255, 255), width=5)

    except Exception as e:
        print(f"⚠️ Avatar konnte nicht geladen werden: {e}")

    # ------------------------------------------------------------
    # BENUTZERNAME HINZUFÜGEN
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
# Top 5 Rank Card erstellen
# ------------------------------------------------------------

async def create_top5_card(ctx: Context[commands.Bot], results: list) -> io.BytesIO:
    """Erstellt ein futuristisches Discord-Ranking-Bild mit korrektem Fortschrittsbalken."""
    width, height = 750, 80 + (len(results) * 130)

    # 🎨 Hintergrund mit leichtem Farbverlauf
    base = Image.new("RGB", (width, height), "#1E1E2E")
    overlay = Image.new("RGB", (width, height), "#2A1A40")
    img = Image.blend(base, overlay, alpha=0.3)
    draw = ImageDraw.Draw(img)

    # Farben und Fonts
    fill_color = "#E0E0E0"
    accent = "#00FFFF"  # Neon-Cyan
    neon_violet = "#9D00FF"
    rank_color = (255, 215, 0, 255)  # Gold


    # 🏆 Titel mit Glow-Effekt
    title_text = "🏆 TOP 5 USER"
    bbox_title = draw.textbbox((0, 0), title_text, font=font_main)
    title_x = (width - (bbox_title[2] - bbox_title[0])) // 2
    draw.text((title_x + 2, 12 + 2), title_text, fill=neon_violet, font=font_main)
    draw.text((title_x, 10), title_text, fill=accent, font=font_main)

    start_y = 80
    avatar_size = 90
    medals = ["🥇", "🥈", "🥉", "🏅", "🎖️"]

    # 🔁 Einträge durchlaufen
    for i, (uid, counter, level) in enumerate(results):
        member = ctx.guild.get_member(int(uid))
        if member is None:
            continue

        y_pos = start_y + (i * 130)
        box_y1, box_y2 = y_pos, y_pos + 110

        # 🔳 Box-Hintergrund mit abgerundeten Ecken
        box = Image.new("RGBA", (width - 40, 110), (40, 40, 60, 220))
        mask = Image.new("L", (width - 40, 110), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 40, 110), radius=20, fill=255)
        img.paste(box, (20, y_pos), mask)

        # 💡 Leichte Neonlinie links
        draw.rectangle([25, y_pos + 10, 30, box_y2 - 10], fill=accent)

        # 🏅 Rang
        rank_text = medals[i] if i < len(medals) else f"#{i+1}"
        draw.text((45, y_pos + 35), rank_text, fill=rank_color, font=font_name)

        # 👤 Avatar mit Glow
        try:
            asset = member.display_avatar.with_format("png").with_size(128)
            data = io.BytesIO(await asset.read())
            avatar_img = Image.open(data).resize((avatar_size, avatar_size)).convert("RGBA")

            # Glow-Effekt
            glow = Image.new("RGBA", (avatar_size + 20, avatar_size + 20), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.ellipse((0, 0, avatar_size + 20, avatar_size + 20), fill=(0, 255, 255, 80))
            img.paste(glow, (130 - 10, y_pos), glow)

            # Runde Maske
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
            img.paste(avatar_img, (130, y_pos + 10), mask)

        except Exception as e:
            print(f"⚠️ Avatar konnte nicht geladen werden für {member.name}: {e}")

        # 📜 Name & Level
        name_x = 130 + avatar_size + 30
        draw.text((name_x, y_pos + 20), member.display_name, fill=fill_color, font=font_name)
        draw.text((name_x, y_pos + 60), f"Level {level} • XP {counter}", fill="#AAAAAA", font=font_small)

        # 📈 Fortschrittsbalken mit richtiger Berechnung
        bar_x1, bar_x2 = name_x, width - 80
        bar_y = y_pos + 90

        # Fortschritt korrekt berechnen
        progress, xp_current, xp_needed = berechne_fortschritt(counter, level)
        progress = max(0.0, min(1.0, progress))  # Clamp auf 0–1

        # Hintergrund des Balkens
        draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, fill=(70, 70, 90))

        # Fortschritt (Cyan → Violett Verlauf)
        bar_width = int((bar_x2 - bar_x1) * progress)
        if bar_width > 0:
            gradient = Image.new("RGB", (bar_width, 10), "#000000")
            grad_draw = ImageDraw.Draw(gradient)
            for x in range(bar_width):
                # Schönerer Übergang: von #00FFFF nach #9D00FF
                r = int(0 + (157 - 0) * (x / bar_width))
                g = int(255 - (255 - 0) * (x / bar_width))
                b = 255
                grad_draw.line((x, 0, x, 10), fill=(r, g, b))
            img.paste(gradient, (bar_x1, bar_y))

        # Glühender Punkt am Ende
        if bar_width > 0:
            glow_radius = 8
            glow = Image.new("RGBA", (glow_radius * 2, glow_radius * 2), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.ellipse((0, 0, glow_radius * 2, glow_radius * 2), fill=(0, 255, 255, 180))
            img.paste(glow, (bar_x1 + bar_width - glow_radius, bar_y - 4), glow)

    # 📦 Ausgabe
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf





# ------------------------------------------------------------
# Cog-Klasse für das Levelsystem 
# ------------------------------------------------------------

class Leveling(commands.Cog):
    """Levelsystem für Nachrichten-Zählung und Rangkarten"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid: 
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
                emoji = discord.utils.get(message.guild.emojis, name="plusmedium")
                if emoji is None:
                    emoji = "➕"  # fallback
                await message.add_reaction(emoji)
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

        # Rang berechnen 
        cursor.execute("SELECT COUNT(*) + 1 FROM user WHERE counter > %s", (counter,))
        rank_res = cursor.fetchone()
        rank = rank_res[0] if rank_res else 1

        cursor.close()
        conn.close()

        image_stream = await create_rank_card(user, counter, level, rank, progress_percent, xp_current_in_level, xp_needed_for_level_up)
        await ctx.send(file=discord.File(image_stream, filename=f"rank_card_{user.name}.png"))


    # ------------------------------------------------------------
    # Top 5 Befehl
    # ------------------------------------------------------------

    @commands.hybrid_command(name="top5", description="Zeigt die Top 5 User im Levelsystem an")
    async def top5(self, ctx: Context[commands.Bot]):
        """Zeigt die Top 5 Benutzer mit dem höchsten Level und XP als Bild an."""
        await ctx.defer()

        conn = db.get_connection()
        cursor = conn.cursor()

        # Top 5 Benutzer anhand ihres Counters (XP)
        cursor.execute("""
            SELECT id, counter, level 
            FROM user 
            ORDER BY counter DESC 
            LIMIT 5
        """)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if not results:
            await ctx.send(embed=discord.Embed(
                title="Noch keine Daten vorhanden 😢",
                description="Es wurden noch keine Nachrichten gezählt.",
                color=discord.Color.red()
            ))
            return

        # 🖼️ BILD ERSTELLEN
        image_stream = await create_top5_card(ctx, results)
        await ctx.send(file=discord.File(image_stream, filename="top5_leaderboard.png"))


# ------------------------------------------------------------
# Cog Setup 
# ------------------------------------------------------------

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))