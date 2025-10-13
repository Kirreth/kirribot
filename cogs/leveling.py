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

def get_base_path(*paths: str) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    return os.path.join(base_dir, *paths)

# Schriftarten laden
try:
    FONT_PATH = get_base_path("assets", "fonts", "RobotoMono-VariableFont_wght.ttf")
    font_main = ImageFont.truetype(FONT_PATH, 40)
    font_small = ImageFont.truetype(FONT_PATH, 30)
except Exception as e:
    print(f"Fehler beim Laden der Schriftart: {e}")
    font_main = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Level anhand Counter berechnen (N²-System: thresholds are 1,4,9,16,...)
def berechne_level(counter: int) -> int:
    if counter < 1:
        return 0
    # level = floor(sqrt(counter))
    level = int(math.sqrt(counter))
    # if counter is exactly a perfect square we are that level, else floor sqrt gives current level
    # we want levels like: 1..3 -> level 1 (since 1^2=1, 2^2=4 -> 2..3 still level1), 
    # but using floor(sqrt) returns 1 for 1..3 (sqrt(3)=1.73 -> 1) which is correct.
    return level

# Fortschritt und verbleibende XP korrekt berechnen, basierend auf N^2 thresholds
def berechne_fortschritt(counter: int, level: int):
    """
    returns (progress_percent (0..1), xp_rest:int)
    level = current level determined by floor(sqrt(counter))
    """
    # Wenn level == 0 behandeln
    if level <= 0:
        prev_threshold = 0
    else:
        prev_threshold = level * level  # level^2

    next_level = level + 1
    next_threshold = next_level * next_level  # (level+1)^2

    xp_in_level = counter - prev_threshold
    xp_needed = next_threshold - prev_threshold  # = (level+1)^2 - level^2 = 2*level + 1
    # Vermeide Division durch Null (falls xp_needed == 0)
    if xp_needed <= 0:
        progress_percent = 1.0
    else:
        progress_percent = max(0.0, min(1.0, xp_in_level / xp_needed))

    xp_rest = max(0, next_threshold - counter)
    return progress_percent, xp_rest

async def create_rank_card(member: discord.User, counter: int, level: int, rank: int, progress_percent: float, xp_left: int) -> io.BytesIO:
    width, height = 800, 200
    img = Image.new("RGB", (width, height), "#000000")
    draw = ImageDraw.Draw(img)

    # Hintergrundbild laden (random 1..5)
    try:
        random_bg = random.randint(1, 5)
        bg_path = get_base_path("images", f"background{random_bg}.png")
        bg_img = Image.open(bg_path).resize((width, height)).convert("RGB")
        img.paste(bg_img, (0, 0))
    except Exception as e:
        print(f"Hintergrund konnte nicht geladen werden: {e}")

    # Avatar
    avatar_size = (150, 150)
    asset = member.display_avatar.with_format("png").with_size(256)
    data = io.BytesIO(await asset.read())
    avatar_img = Image.open(data).resize(avatar_size).convert("RGB")
    img.paste(avatar_img, (25, 25))

    # Text: Level | Rank | XP (weiß)
    fill_color = "#FFFFFF"
    draw.text((200, 30), f"Level: {level}", fill=fill_color, font=font_main)
    draw.text((400, 30), f"Rank: {rank}", fill=fill_color, font=font_main)
    draw.text((600, 30), f"XP: {counter}", fill=fill_color, font=font_main)

    # Fortschrittsbalken
    bar_x, bar_y = 200, 120
    bar_width = 550
    bar_height = 25
    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill="#333333")
    draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * progress_percent), bar_y + bar_height], fill="#ffffff")

    # Optional Balken-Linien
    step = 15
    for i in range(0, bar_width, step):
        draw.line([(bar_x + i, bar_y), (bar_x + i, bar_y + bar_height)], fill="#111111", width=1)

    # Text unter Balken: Noch X Nachrichten
    #draw.text((bar_x, bar_y + 35), f"Noch {xp_left} Nachrichten bis Level {level + 1}", fill=fill_color, font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="png")
    buf.seek(0)
    return buf

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

        if result is None:
            counter = 1
        else:
            counter = result[0] + 1

        level = berechne_level(counter)

        if result is None:
            cursor.execute("INSERT INTO user (id, name, counter, level) VALUES (%s, %s, %s, %s)", (uid, uname, counter, level))
        else:
            cursor.execute("UPDATE user SET counter=%s, level=%s WHERE id=%s", (counter, level, uid))

        conn.commit()
        cursor.close()
        conn.close()

    @commands.hybrid_command(name="rank", description="Zeigt das Profil des Users im Matrix-Style")
    async def rank(self, ctx: Context[commands.Bot], user: Optional[Union[discord.User, discord.Member]] = None):
        user = user or ctx.author
        uid = str(user.id)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id=%s", (uid,))
        result = cursor.fetchone()
        if not result:
            await ctx.send(embed=discord.Embed(title=f"{user.name} hat noch keine Nachrichten geschrieben.", color=discord.Color.red()))
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

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
