import discord
from discord.ext import commands, tasks
from utils import database as db
from datetime import datetime

class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_active_users.start()  # startet Loop automatisch

    def cog_unload(self):
        self.check_active_users.cancel()

    @tasks.loop(minutes=5)  # alle 5 Minuten prüfen
    async def check_active_users(self):
        for guild in self.bot.guilds:
            active_members = [
                m for m in guild.members
                if not m.bot and m.status != discord.Status.offline
            ]
            count = len(active_members)
            db.set_max_active(str(guild.id), count)  # prüft & speichert nur, wenn höher

    @check_active_users.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityTracker(bot))
