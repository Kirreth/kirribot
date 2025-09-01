import discord
from discord.ext import commands
from discord import app_commands
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

    @app_commands.command(name="topb", description="Zeigt deine gesamte Anzahl an Bumps")
    async def topb(
        self,
        interaction: discord.Interaction,
        user: Optional[Union[discord.User, discord.Member]] = None
    ) -> None:
        user = user or interaction.user
        if user is None:
            return
        user_id: str = str(user.id)
        guild_id: str = str(interaction.guild.id) if interaction.guild else "0"
        count: int = db.get_bumps_total(user_id, guild_id)
        await interaction.response.send_message(
            f"📈 {user.mention} hat insgesamt **{count} Bumps** gemacht."
        )

    @app_commands.command(name="topmb", description="Zeigt deine Anzahl an Bumps der letzten 30 Tage")
    async def topmb(
        self,
        interaction: discord.Interaction,
        user: Optional[Union[discord.User, discord.Member]] = None
    ) -> None:
        user = user or interaction.user
        if user is None:
            return
        user_id: str = str(user.id)
        guild_id: str = str(interaction.guild.id) if interaction.guild else "0"
        count: int = db.get_bumps_30d(user_id, guild_id)
        await interaction.response.send_message(
            f"⏳ {user.mention} hat in den letzten 30 Tagen **{count} Bumps** gemacht."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bumps(bot))
