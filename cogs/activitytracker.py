import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from utils import database as db
from typing import Optional

class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_active_users.start() 

    def cog_unload(self):
        self.check_active_users.cancel()

    @tasks.loop(minutes=5)
    async def check_active_users(self):
        for guild in self.bot.guilds:
            active_members = [
                m for m in guild.members
                if not m.bot and m.status != discord.Status.offline
            ]
            count = len(active_members)
            db.set_max_active(str(guild.id), count) 

    @check_active_users.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        db.log_command_usage(ctx.command.qualified_name, str(ctx.guild.id) if ctx.guild else "DM")

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command
    ):
        db.log_command_usage(command.qualified_name, str(interaction.guild.id) if interaction.guild else "DM")

    @commands.hybrid_command(name="topcommands", description="Zeigt die am häufigsten genutzten Befehle")
    async def topcommands(self, ctx: Context[commands.Bot], limit: Optional[int] = 5) -> None:
        guild_id = str(ctx.guild.id) if ctx.guild else "DM"
        results = db.get_top_commands(guild_id, limit)
        if not results:
            await ctx.send("Keine Befehle wurden bisher genutzt.")
            return
        embed = discord.Embed(title="📊 Top Befehle", color=discord.Color.green())
        for idx, (cmd, uses) in enumerate(results, start=1):
            embed.add_field(name=f"{idx}. {cmd}", value=f"✅ {uses} Aufrufe", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="mr", description="Zeigt den Rekord der meisten Mitglieder")
    async def mr(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        record = db.get_max_members(guild_id)
        if record:
            await ctx.send(f"👥 Rekord-Mitgliederzahl: **{record}**")
        else:
            await ctx.send("Es wurde noch kein Mitgliederrekord gespeichert.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityTracker(bot))
