# cogs/activitytracker.py
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
# Stellen Sie sicher, dass Sie db_users korrekt importieren
from utils.database import users as db_users, commands as db_commands, messages as db_messages 
from typing import Optional

class ActivityTracker(commands.Cog):
    """Verfolgt die Aktivität der Nutzer auf dem Server"""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_active_users.start() 
        self.check_total_members.start() 

    def cog_unload(self):
        self.check_active_users.cancel()
        self.check_total_members.cancel()

    # ------------------------------------------------------------
    # Aktive User Check (Alle 5 Minuten)
    # ------------------------------------------------------------
    @tasks.loop(minutes=5)
    async def check_active_users(self):
        for guild in self.bot.guilds:
            active_members = [
                m for m in guild.members
                if not m.bot and m.status != discord.Status.offline
            ]
            count = len(active_members)
            
            # --- DEBUG-AUSGABE: Prüft, welcher Wert an die DB gesendet wird ---
            # print(f"DEBUG: Active count for {guild.name} ({guild.id}): {count}")
            # ---------------------------------------------------------------------

            # Speichert den Rekord der AKTIVEN Nutzer (in 'active_users' Tabelle)
            # Nutzt guild_id: str(guild.id)
            db_users.set_max_active(str(guild.id), count) 

    @tasks.loop(minutes=5.0)
    async def check_total_members(self):
        """Überprüft und speichert den Rekord der Gesamtmitgliederanzahl."""
        for guild in self.bot.guilds:
            if guild.unavailable:
                continue
            
            # Gesamtmitgliederzahl (inkl. Bots)
            total_count = guild.member_count 
            
            # Speichert den Rekord der GESAMTMITGLIEDER (in 'members' Tabelle)
            # Nutzt guild_id: str(guild.id)
            db_users.set_max_members(str(guild.id), total_count)


    @check_active_users.before_loop
    @check_total_members.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # ============================================================
    # Listener: Loggt Kanalaktivität
    # ============================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignoriere Bots und DMs
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)

        # Loggt Kanal-Aktivität (nutzt guild_id, user_id, channel_id für den UNIQUE KEY)
        # 🚩 KEINE ÄNDERUNG NÖTIG: Der Aufruf ist korrekt.
        db_messages.log_channel_activity(channel_id, guild_id, user_id)
        # Levelsystem XP-Logik wurde entfernt.


    # ------------------------------------------------------------
    # Listener: Normale Befehle (Prefix) - NUR COMMAND USAGE LOGGEN
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_command(self, ctx: Context[commands.Bot]):
        if not ctx.guild:
            return 
        
        guild_id = str(ctx.guild.id)
        
        # Befehlsnutzung protokollieren
        # Nutzt command_name und guild_id
        db_commands.log_command_usage(ctx.command.qualified_name, guild_id)


    # ------------------------------------------------------------
    # Listener: Slash Commands (App Commands)
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command
    ):
        if not interaction.guild:
            return 
        
        guild_id = str(interaction.guild.id)
        
        # 1. Befehlsnutzung protokollieren
        # Nutzt command_name und guild_id
        db_commands.log_command_usage(command.qualified_name, guild_id)
        
        # 2. Loggt Kanal-Aktivität (Soll zählen)
        if interaction.channel and interaction.user:
            user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)

            # Loggt Kanal-Aktivität (nutzt guild_id, user_id, channel_id für den UNIQUE KEY)
            db_messages.log_channel_activity(channel_id, guild_id, user_id)


# ------------------------------------------------------------
# Hybrid Commands (topcommands, mr, mrr, topc)
# ------------------------------------------------------------

#-------------
# Am häufigsten genutzte Commands
#-------------
    @commands.hybrid_command(name="topcommands", description="Zeigt die am häufigsten genutzten Befehle")
    async def topcommands(self, ctx: Context[commands.Bot], limit: Optional[int] = 5) -> None:
        if not ctx.guild:
              await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
              return
              
        guild_id = str(ctx.guild.id)
        # Holt Top Commands basierend auf guild_id
        results = db_commands.get_top_commands(guild_id, limit)
        
        if not results:
            await ctx.send("Keine Befehle wurden bisher genutzt.")
            return
            
        embed = discord.Embed(title="📊 Top Befehle", color=discord.Color.green())
        for idx, (cmd, uses) in enumerate(results, start=1):
            embed.add_field(name=f"{idx}. /{cmd}", value=f"✅ {uses} Aufrufe", inline=False)
            
        await ctx.send(embed=embed)

#-------------
# Mitgliederrekord (Aktive Nutzer)
#-------------
    @commands.hybrid_command(name="mr", description="Zeigt den Rekord der aktivsten Mitglieder")
    async def mr(self, ctx: Context[commands.Bot]):
        if not ctx.guild:
              await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
              return
              
        guild_id = str(ctx.guild.id)
        # Ruft den Rekord der AKTIVEN Mitglieder ab
        record = db_users.get_max_active(guild_id) 
        
        if record and record != "0": # Prüfen auf gespeicherten Wert
            # Die Task zählt aktive Mitglieder
            await ctx.send(f"👥 Rekord der **aktiven** Mitglieder: **{record}**")
        else:
            await ctx.send("Es wurde noch kein Rekord der aktiven Mitglieder gespeichert.")
            
#-------------
# Mitgliederrekord (Gesamtanzahl)
#-------------
    @commands.hybrid_command(name="mrr", description="Zeigt den Rekord der gesamten Mitgliederanzahl auf dem Server.")
    async def mrr(self, ctx: commands.Context):
        if not ctx.guild:
              return await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
              
        guild_id = str(ctx.guild.id)
        # Ruft den Rekord der GESAMTEN Mitglieder ab
        record = db_users.get_max_members(guild_id) 
        
        if record and record != "0": # Prüfen auf gespeicherten Wert
              await ctx.send(f"📈 Rekord der **gesamten** Mitglieder: **{record}**")
        else:
              await ctx.send("Es wurde noch kein Rekord der gesamten Mitglieder gespeichert.")

#-------------
# Top 5 Channel (Aktivität)
#-------------
    @commands.hybrid_command(name="topc", description="Zeigt die 5 aktivsten Channels des Servers")
    async def topc(self, ctx: Context[commands.Bot]):
        if not ctx.guild:
              await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.")
              return
              
        guild_id = str(ctx.guild.id)
        # Holt Top Channels basierend auf guild_id
        results = db_messages.get_top_channels(guild_id, 5)
        
        if not results:
            await ctx.send("📊 Es gibt noch keine Aktivität in den Channels.")
            return
            
        embed = discord.Embed(title="🏆 Top 5 Aktivste Channels", color=discord.Color.blurple())
        
        for idx, (channel_id, count) in enumerate(results, start=1):
            channel = ctx.guild.get_channel(int(channel_id))
            # Verwende den Namen des Channels, wenn er existiert, ansonsten eine Fallback-Meldung
            name = channel.mention if channel else f"Gelöscht ({channel_id})"
            embed.add_field(name=f"{idx}. {name}", value=f"💬 {count} Aktionen", inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityTracker(bot))