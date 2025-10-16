# cogs/activitytracker.py
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from utils.database import users as db_users, commands as db_commands, messages as db_messages
from typing import Optional

class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_active_users.start() 

    def cog_unload(self):
        self.check_active_users.cancel()

    # ------------------------------------------------------------
    # Aktive User Check (Alle 5 Minuten)
    # ------------------------------------------------------------

    @tasks.loop(minutes=5)
    async def check_active_users(self):
        for guild in self.bot.guilds:
            # Stelle sicher, dass wir nur Mitglieder prüfen, die keine Bots sind und nicht offline sind
            active_members = [
                m for m in guild.members
                if not m.bot and m.status != discord.Status.offline
            ]
            count = len(active_members)
            # db_users.set_max_active übernimmt die Logik für max_active und max_active_log
            db_users.set_max_active(str(guild.id), count) 

    @check_active_users.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------
    # Listener: Normale Befehle (Prefix)
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_command(self, ctx: Context[commands.Bot]):
        # Prüfen, ob der Befehl in einem Server ausgeführt wurde
        if not ctx.guild:
            return # DM-Befehle für diese Logs ignorieren oder gesondert behandeln
        
        guild_id = str(ctx.guild.id)
        
        # 1. Befehlsnutzung protokollieren
        db_commands.log_command_usage(ctx.command.qualified_name, guild_id)
        
        # 2. Kanalaktivität protokollieren (muss Channel-ID haben)
        if ctx.channel:
             # user_id ist erforderlich für die 'messages'-Tabelle
            user_id = str(ctx.author.id)
            db_messages.log_channel_activity(str(ctx.channel.id), guild_id, user_id)


    # ------------------------------------------------------------
    # Listener: Slash Commands (App Commands)
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command
    ):
        # Prüfen, ob die Interaktion in einem Server stattfand
        if not interaction.guild:
            return # DM-Befehle für diese Logs ignorieren
        
        guild_id = str(interaction.guild.id)
        
        # 1. Befehlsnutzung protokollieren
        db_commands.log_command_usage(command.qualified_name, guild_id)
        
        # 2. Kanalaktivität protokollieren (war die Quelle des IntegrityError)
        if interaction.channel and interaction.user:
            # user_id ist erforderlich für die 'messages'-Tabelle
            user_id = str(interaction.user.id)
            # Wenn log_channel_activity auch die user_id benötigt, muss sie übergeben werden.
            db_messages.log_channel_activity(str(interaction.channel.id), guild_id, user_id)

# ------------------------------------------------------------
# Topcommands
# ------------------------------------------------------------

    @commands.hybrid_command(name="topcommands", description="Zeigt die am häufigsten genutzten Befehle")
    async def topcommands(self, ctx: Context[commands.Bot], limit: Optional[int] = 5) -> None:
        # Hier muss ctx.guild geprüft werden, da DM-Befehle erlaubt sind, aber die DB-Logik guild_id benötigt
        if not ctx.guild:
             await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
             return
             
        guild_id = str(ctx.guild.id)
        results = db_commands.get_top_commands(guild_id, limit)
        
        if not results:
            await ctx.send("Keine Befehle wurden bisher genutzt.")
            return
            
        embed = discord.Embed(title="📊 Top Befehle", color=discord.Color.green())
        for idx, (cmd, uses) in enumerate(results, start=1):
            embed.add_field(name=f"{idx}. {cmd}", value=f"✅ {uses} Aufrufe", inline=False)
            
        await ctx.send(embed=embed)

# ------------------------------------------------------------
# Userrekord
# ------------------------------------------------------------

    @commands.hybrid_command(name="mr", description="Zeigt den Rekord der meisten Mitglieder")
    async def mr(self, ctx: Context[commands.Bot]):
        if not ctx.guild:
             await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
             return
             
        guild_id = str(ctx.guild.id)
        record = db_users.get_max_members(guild_id)
        
        if record:
            await ctx.send(f"👥 Rekord-Mitgliederzahl: **{record}**")
        else:
            await ctx.send("Es wurde noch kein Mitgliederrekord gespeichert.")

    @commands.hybrid_command(name="topc", description="Zeigt die 5 aktivsten Channels des Servers")
    async def topc(self, ctx: Context[commands.Bot]):
        if not ctx.guild:
             await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
             return
             
        guild_id = str(ctx.guild.id)
        results = db_messages.get_top_channels(guild_id, 5)
        
        if not results:
            await ctx.send("📊 Es gibt noch keine Aktivität in den Channels.")
            return
            
        embed = discord.Embed(title="🏆 Top 5 Aktivste Channels", color=discord.Color.blurple())
        
        for idx, (channel_id, count) in enumerate(results, start=1):
            channel = ctx.guild.get_channel(int(channel_id))
            name = channel.mention if channel else f"Gelöscht ({channel_id})"
            embed.add_field(name=f"{idx}. {name}", value=f"💬 {count} Aktionen", inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityTracker(bot))