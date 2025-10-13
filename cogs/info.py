# cogs/info.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional
from datetime import datetime
from utils import database as db

class Info(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userinfo",
        description="Zeigt Infos über einen Benutzer"
    )
    async def userinfo(self, ctx: Context[commands.Bot], user: discord.Member) -> None:
        embed = discord.Embed(
            title=f"Infos über {user.name}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="Name", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Bot?", value="✅ Ja" if user.bot else "❌ Nein", inline=True)
        embed.add_field(name="Account erstellt", value=user.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)
        if user.joined_at:
            embed.add_field(name="Beigetreten", value=user.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)

        # Rollen
        roles: list[str] = []
        if ctx.guild:
            default_role = getattr(ctx.guild, "default_role", None)
            roles = [role.mention for role in user.roles if role != default_role]

        embed.add_field(name="Rollen", value=", ".join(roles) if roles else "Keine Rollen", inline=False)

        # Leveling-Daten
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter, level FROM user WHERE id = %s", (str(user.id),))
        result = cursor.fetchone()
        conn.close()

        if result:
            counter, level = result
            embed.add_field(name="Nachrichten", value=f"{counter} Nachrichten", inline=True)
            embed.add_field(name="Level", value=f"🆙 Level {level}", inline=True)

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="aur",
        description="Zeigt den Höchstwert gleichzeitiger aktiver User im Server"
    )
    async def aur(self, ctx: Context[commands.Bot]) -> None:
        if not ctx.guild:
            await ctx.send("Dieser Befehl kann nur in einem Server benutzt werden.", ephemeral=True)
            return

        guild_id = str(ctx.guild.id)
        max_active = db.get_max_active(guild_id)

        if max_active == 0:
            await ctx.send("📊 Es wurden bisher keine aktiven User gezählt.")
            return

        # Timestamp (falls gespeichert)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp FROM max_active WHERE guild_id=?", (guild_id,))
        row = cursor.fetchone()
        conn.close()

        timestamp = row[0] if row else None
        date_str = datetime.fromisoformat(timestamp).strftime("%d.%m.%Y %H:%M:%S") if timestamp else "Unbekannt"

        embed = discord.Embed(
            title=f"📈 Aktiver Nutzer-Rekord für {ctx.guild.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="👥 Höchstwert", value=f"{max_active} gleichzeitige Nutzer", inline=False)
        embed.add_field(name="📅 Zeitpunkt", value=date_str, inline=False)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))
