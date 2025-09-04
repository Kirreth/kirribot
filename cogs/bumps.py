import discord
from discord.ext import commands
from datetime import datetime
from utils import database as db
from typing import Optional, Union

DISBOARD_ID: int = 302050872383242240

class Bumps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.id != DISBOARD_ID:
            return

        if "Bump done" in message.content or "Bump erfolgreich" in message.content:
            if message.interaction and message.interaction.user:
                bumper: Union[discord.User, discord.Member] = message.interaction.user
            else:
                return

            user_id: str = str(bumper.id)
            guild_id: str = str(message.guild.id) if message.guild else "0"
            db.log_bump(user_id, guild_id, datetime.utcnow())
            print(f"✅ Bump von {bumper} gespeichert")

    @commands.hybrid_command(
        name="topb",
        description="Zeigt die Top 3 mit den meisten Bumps insgesamt"
    )
    async def topb(self, ctx: commands.Context) -> None:
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        top_users = db.get_bump_top(guild_id, days=None, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Bumps in diesem Server.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            user = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            username = user.mention if user else f"Unbekannt ({user_id})"
            description += f"**#{index}** {username} – **{count} Bumps**\n"

        embed = discord.Embed(
            title="🏆 Top 3 Bumper (Gesamt)",
            description=description,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="topmb",
        description="Zeigt die Top 3 mit den meisten Bumps in den letzten 30 Tagen"
    )
    async def topmb(self, ctx: commands.Context) -> None:
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        top_users = db.get_bump_top(guild_id, days=30, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Bumps in den letzten 30 Tagen.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            user = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            username = user.mention if user else f"Unbekannt ({user_id})"
            description += f"**#{index}** {username} – **{count} Bumps**\n"

        embed = discord.Embed(
            title="⏳ Top 3 Bumper (Letzte 30 Tage)",
            description=description,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bumps(bot))
