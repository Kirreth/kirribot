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

# ------------------------------------------------------------
# Info über User
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# Rollen des Users
# ------------------------------------------------------------

        roles: list[str] = []
        if ctx.guild:
            default_role = getattr(ctx.guild, "default_role", None)
            roles = [role.mention for role in user.roles if role != default_role]

        embed.add_field(name="Rollen", value=", ".join(roles) if roles else "Keine Rollen", inline=False)

# ------------------------------------------------------------
# Level des Users
# ------------------------------------------------------------

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))
