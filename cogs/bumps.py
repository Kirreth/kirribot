import discord
from discord.ext import commands, tasks
from discord.utils import utcnow
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, List, Tuple
from utils.database import bumps as db_bumps
from utils.database import guilds as db_guilds

from discord.ext.commands import Context
from PIL import Image, ImageDraw, ImageFont
import io
import os
import math
import random

DISBOARD_ID: int = 302050872383242240
BUMP_COOLDOWN: timedelta = timedelta(hours=2)

def get_base_path(*paths: str) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    return os.path.join(base_dir, *paths)

try:
    FONT_PATH = get_base_path("assets", "fonts", "RobotoMono-VariableFont_wght.ttf")
    font_main = ImageFont.truetype(FONT_PATH, 40)
    font_small = ImageFont.truetype(FONT_PATH, 25) 
    font_tiny = ImageFont.truetype(FONT_PATH, 20)
    font_name = ImageFont.truetype(FONT_PATH, 30) 
except Exception as e:
    font_main = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_tiny = ImageFont.load_default()
    font_name = ImageFont.load_default()

async def create_bump_card(ctx, results: list, total_bumps: int) -> io.BytesIO:
    width, height = 750, 80 + (len(results) * 130)

    base = Image.new("RGB", (width, height), "#2B1A2E")
    overlay = Image.new("RGB", (width, height), "#1A0C33")
    img = Image.blend(base, overlay, alpha=0.35)
    draw = ImageDraw.Draw(img)

    fill_color = "#F0E6FF"
    accent = "#FF007A"
    accent2 = "#FF087B"

    title_text = "🔥 TOP BUMPERS"
    bbox_title = draw.textbbox((0, 0), title_text, font=font_main)
    title_x = (width - (bbox_title[2] - bbox_title[0])) // 2
    draw.text((title_x, 10), title_text, fill=accent, font=font_main)

    start_y = 80
    avatar_size = 90
    medals = ["🔥", "⚡", "🚀", "✨", "💠"]

    for i, (uid, bumps) in enumerate(results):
        member = ctx.guild.get_member(int(uid))
        if not member:
            continue

        y_pos = start_y + (i * 130)

        card = Image.new("RGBA", (width - 40, 110), (60, 30, 80, 220))
        mask = Image.new("L", (width - 40, 110), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 40, 110), radius=22, fill=255)
        img.paste(card, (20, y_pos), mask)

        draw.rectangle([25, y_pos + 10, 30, y_pos + 100], fill=accent)

        rank_text = medals[i] if i < len(medals) else f"#{i+1}"
        draw.text((45, y_pos + 35), rank_text, fill=accent2, font=font_name)

        try:
            asset = member.display_avatar.with_format("png").with_size(128)
            data = io.BytesIO(await asset.read())
            avatar_img = Image.open(data).resize((avatar_size, avatar_size)).convert("RGBA")

            mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

            img.paste(avatar_img, (130, y_pos + 10), mask)

        except Exception as e:
            pass

        name_x = 130 + avatar_size + 30
        draw.text((name_x, y_pos + 20), member.display_name, fill=fill_color, font=font_name)
        draw.text((name_x, y_pos + 60), f"Bumps: {bumps}", fill="#DDDDDD", font=font_small)

        bar_x1, bar_x2 = name_x, width - 80
        bar_y = y_pos + 90
        progress = bumps / total_bumps if total_bumps > 0 else 0

        draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, fill=(80, 50, 100))

        bar_width = int((bar_x2 - bar_x1) * progress)
        if bar_width > 0:
            gradient = Image.new("RGB", (bar_width, 10))
            g = ImageDraw.Draw(gradient)
            for x in range(bar_width):
                r = int(255)
                g_val = int(0 + (179 * (x / bar_width)))
                b_val = int(122 - (122 * (x / bar_width)))
                g.line((x, 0, x, 10), fill=(r, g_val, b_val))
            img.paste(gradient, (bar_x1, bar_y))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf



class Bumps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not self.bump_reminder_check.is_running():
            self.bump_reminder_check.start()

    def cog_unload(self) -> None:
        self.bump_reminder_check.cancel()

    async def smart_send(self, ctx: commands.Context, /, **kwargs):
        if getattr(ctx, "_reply_sent", False):
            return

        interaction = getattr(ctx, "interaction", None)
        try:
            if interaction:
                if not interaction.response.is_done():
                    await interaction.response.send_message(**kwargs)
                else:
                    await interaction.followup.send(**kwargs)
            else:
                kwargs.pop("ephemeral", None)
                await ctx.reply(**kwargs)
        finally:
            setattr(ctx, "_reply_sent", True)

    @tasks.loop(seconds=1)
    async def bump_reminder_check(self) -> None:
        try:
            guild_settings = db_bumps.get_all_guild_settings_with_roles()
        except Exception as e:
            print(f"[ERROR] Fehler beim Abrufen aller Guild-Einstellungen: {e}")
            return

        now_utc = utcnow()

        for guild_id_str, reminder_channel_id, bumper_role_id, reminder_status in guild_settings:
            if not reminder_channel_id:
                continue

            last_bump_time: Optional[datetime] = db_bumps.get_last_bump_time(guild_id_str)
            if last_bump_time is None:
                continue

            if last_bump_time.tzinfo is None:
                last_bump_time = last_bump_time.replace(tzinfo=timezone.utc)

            next_bump_time = last_bump_time + BUMP_COOLDOWN
            if now_utc < next_bump_time:
                continue

            if reminder_status:
                continue

            channel = self.bot.get_channel(reminder_channel_id)
            if not channel:
                continue

            bumper_role_mention = ""
            guild = self.bot.get_guild(int(guild_id_str))
            
            if guild and bumper_role_id:
                role = guild.get_role(int(bumper_role_id))
                if role:
                    bumper_role_mention = role.mention

            try:
                await channel.send(
                    f"⏰ **Bump-Zeit!** Der 2-stündige Cooldown ist abgelaufen.\n"
                    f"{bumper_role_mention} – jemand kann jetzt `/bump` nutzen! "
                    f"<t:{int(next_bump_time.timestamp())}:R>"
                )
                db_bumps.set_reminder_status(guild_id_str, True)
            except discord.Forbidden:
                print(f"[ERROR] Keine Berechtigung, in Channel {reminder_channel_id} zu schreiben.")
            except Exception as e:
                print(f"[ERROR] Fehler beim Senden der Erinnerung: {e}")

    @bump_reminder_check.before_loop
    async def before_bump_reminder_check(self) -> None:
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        try:
            if message.author.id != DISBOARD_ID or not message.guild:
                return
            
            is_success_message = "Bump done" in message.content or "Bump erfolgreich" in message.content
            if not is_success_message and message.embeds:
                embed = message.embeds[0]
                embed_text = (embed.title or "") + (embed.description or "")
                if "Bump done" in embed_text or "Bump erfolgreich" in embed_text:
                    is_success_message = True
            
            if not is_success_message:
                return
            
            bumper: Optional[Union[discord.User, discord.Member]] = None
            if getattr(message, "interaction_metadata", None) and message.interaction_metadata.user:
                bumper = message.interaction_metadata.user
            elif message.mentions:
                bumper = message.mentions[0]
            else:
                return

            user_id = str(bumper.id)
            guild_id = str(message.guild.id)
            current_time = utcnow()

            # Entfernt, da die Tabelle 'bump_logs' laut Fehlermeldung fehlt:
            # db_bumps.log_bump(user_id, guild_id, current_time)
            
            db_bumps.increment_total_bumps(user_id, guild_id)
            
            db_bumps.set_last_bump_time(guild_id, current_time)
            db_bumps.set_reminder_status(guild_id, False) 
        except Exception as e:
            print(f"[ERROR] Fehler beim Verarbeiten der Bump-Nachricht: {e}")

            
    @commands.hybrid_command(
        name="nextbump",
        description="Zeigt an, wann der nächste Disboard Bump möglich ist."
    )
    async def nextbump(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            return await self.smart_send(ctx, content="Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)

        if getattr(ctx, "interaction", None):
            await ctx.defer()

        guild_id = str(ctx.guild.id)
        last_bump_time: Optional[datetime] = db_bumps.get_last_bump_time(guild_id)

        if last_bump_time is None:
            embed = discord.Embed(
                title="⏳ Nächster Bump",
                description="Der Server wurde noch nicht gebumpt. **Du kannst sofort bumpen!**",
                color=discord.Color(int("24B8B8", 16))
            )
            return await self.smart_send(ctx, embed=embed)

        if last_bump_time.tzinfo is None:
            last_bump_time = last_bump_time.replace(tzinfo=timezone.utc)
        next_bump_time = last_bump_time + BUMP_COOLDOWN
        now_utc = utcnow()

        if now_utc >= next_bump_time:
            embed = discord.Embed(
                title="✅ Nächster Bump",
                description="**Der Cooldown ist abgelaufen!** Du kannst jetzt sofort `/bump` nutzen.",
                color=discord.Color(int("24B8B8", 16))
            )
        else:
            time_remaining = next_bump_time - now_utc
            total_seconds = int(time_remaining.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 1:
                time_str = f"{hours} Stunden und {minutes} Minuten"
            elif hours == 1:
                time_str = f"1 Stunde und {minutes} Minuten"
            else:
                time_str = f"{minutes} Minuten"

            embed = discord.Embed(
                title="⏳ Nächster Bump",
                description=f"Der nächste Bump ist **<t:{int(next_bump_time.timestamp())}:R>** möglich.\n\n",
                color=discord.Color(int("24B8B8", 16))
            )

        await self.smart_send(ctx, embed=embed)

    @commands.hybrid_command(
        name="topb",
        description="Zeigt die Top 5 mit den meisten Bumps insgesamt als Bild an"
    )
    async def topb(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            return await self.smart_send(ctx, content="Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)

        if getattr(ctx, "interaction", None):
            await ctx.defer()

        guild_id = str(ctx.guild.id)
        
        top_users = db_bumps.get_bump_top(guild_id, days=None, limit=5)
        
        try:
            total_bumps = db_bumps.get_total_bumps_in_guild(guild_id)
        except Exception:
            total_bumps = 0

        if not top_users:
            return await self.smart_send(ctx, content="📊 Es gibt noch keine Bumps in diesem Server.")
            
        active_top_users = []
        for user_id, count in top_users:
            try:
                member = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
                if member:
                    active_top_users.append((user_id, count))
            except Exception:
                continue
        
        if not active_top_users:
            return await self.smart_send(ctx, content="📊 Die Top-Bumper haben alle den Server verlassen oder konnten nicht gefunden werden.", ephemeral=True)

        image_stream = await create_bump_card(ctx, active_top_users, total_bumps)
        await self.smart_send(ctx, file=discord.File(image_stream, filename="top_bumper_leaderboard.png"))

    @commands.hybrid_command(
        name="topmb",
        description="Zeigt die Top 3 mit den meisten Bumps in den letzten 30 Tagen"
    )
    async def topmb(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            return await self.smart_send(ctx, content="Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)

        if getattr(ctx, "interaction", None):
            await ctx.defer()

        guild_id = str(ctx.guild.id)
        top_users = db_bumps.get_bump_top(guild_id, days=30, limit=3)

        if not top_users:
            return await self.smart_send(ctx, content="📊 Es gibt noch keine Bumps in den letzten 30 Tagen.")

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            try:
                user = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            except Exception:
                user = None
            username = user.mention if user else f"Unbekannt ({user_id})"
            description += f"**#{index}** {username} – **{count} Bumps**\n"

        embed = discord.Embed(
            title="⏳ Top 3 Bumper (Letzte 30 Tage)",
            description=description,
            color=discord.Color(int("24B8B8", 16))
        )

        await self.smart_send(ctx, embed=embed)

    @commands.hybrid_command(
        name="getbumprole",
        description="Weise dir die Bumper-Rolle selbst zu."
    )
    async def getbumprole(self, ctx: commands.Context) -> None:
        if not ctx.guild: return
        guild_id = str(ctx.guild.id)
        role_id = db_guilds.get_bumper_role(guild_id) 
        if not role_id:
            return await self.smart_send(ctx, content="❌ Keine Bumper-Rolle für diesen Server festgelegt.", ephemeral=True)

        role = ctx.guild.get_role(int(role_id))
        if not role:
            return await self.smart_send(ctx, content="⚠️ Die gespeicherte Bumper-Rolle existiert nicht mehr.", ephemeral=True)

        member = ctx.author
        if role in member.roles:
            return await self.smart_send(ctx, content="✅ Du hast die Bumper-Rolle bereits!", ephemeral=True)

        try:
            await member.add_roles(role, reason="Selbst zugewiesene Bumper-Rolle")
            await self.smart_send(ctx, content=f"🎉 Du hast die Rolle {role.mention} erhalten!", ephemeral=True)
        except discord.Forbidden:
            await self.smart_send(ctx, content="⚠️ Ich habe keine Berechtigung, dir die Rolle zu geben.", ephemeral=True)

    @commands.hybrid_command(
        name="delbumprole",
        description="Entfernt die Bumper-Rolle von dir selbst."
    )
    async def delbumprole(self, ctx: commands.Context) -> None:
        if not ctx.guild: return
        guild_id = str(ctx.guild.id)
        role_id = db_guilds.get_bumper_role(guild_id) 
        if not role_id:
            return await self.smart_send(ctx, content="❌ Keine Bumper-Rolle für diesen Server festgelegt.", ephemeral=True)

        role = ctx.guild.get_role(int(role_id))
        if not role:
            return await self.smart_send(ctx, content="⚠️ Die gespeicherte Bumper-Rolle existiert nicht mehr.", ephemeral=True)

        member = ctx.author
        if role not in member.roles:
            return await self.smart_send(ctx, content="ℹ️ Du hast die Bumper-Rolle nicht.", ephemeral=True)
        else:
            try:
                await member.remove_roles(role, reason="Selbst entfernt")
                await self.smart_send(ctx, content=f"❌ Die Rolle {role.mention} wurde entfernt.", ephemeral=True)
            except discord.Forbidden:
                await self.smart_send(ctx, content="⚠️ Ich habe keine Berechtigung, die Rolle zu entfernen.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bumps(bot))