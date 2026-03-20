# cogs/counter.py
import discord
from discord.ext import commands
from discord import app_commands
from utils.database import counter as db_counter

class Counter(commands.Cog):
    """Verwaltet und zeigt Wort-Statistiken für den Server an"""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------
    # Listener: Überwacht jede Nachricht auf registrierte Wörter
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignoriere Bots und Direktnachrichten
        if message.author.bot or not message.guild:
            return
        
        # Datenbank-Abgleich und Hochzählen
        db_counter.increment_all_matches(str(message.guild.id), message.content)

    # ------------------------------------------------------------
    # Befehl: Wort zum Zähler hinzufügen
    # ------------------------------------------------------------
    @app_commands.command(
        name="counter_add", 
        description="Fügt ein Wort hinzu, das ab jetzt gezählt werden soll"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def counter_add(self, interaction: discord.Interaction, wort: str):
        guild_id = str(interaction.guild_id)
        word_clean = wort.strip().lower()

        if db_counter.add_new_counter(guild_id, word_clean):
            await interaction.response.send_message(
                f"✅ Erfolg! Ich zähle ab sofort jedes Mal, wenn `{word_clean}` geschrieben wird.", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ Das Wort `{word_clean}` wird bereits gezählt.", 
                ephemeral=True
            )

    # ------------------------------------------------------------
    # Befehl: Statistiken anzeigen
    # ------------------------------------------------------------
    @app_commands.command(
        name="show_counters", 
        description="Zeigt die Rangliste der gezählten Wörter auf diesem Server"
    )
    async def show_counters(self, interaction: discord.Interaction):
        stats = db_counter.get_counter_stats(str(interaction.guild_id))

        if not stats:
            await interaction.response.send_message(
                "Es wurden noch keine Wörter für diesen Server registriert. Nutze `/counter_add`!", 
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📊 Wort-Counter Statistik: {interaction.guild.name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Erstelle eine formatierte Liste für das Embed
        # Wir zeigen die Top 15 Wörter an, falls die Liste sehr lang ist
        description_text = ""
        for idx, (word, count) in enumerate(stats[:15], start=1):
            description_text += f"**{idx}. {word.capitalize()}**: `{count}` mal\n"
        
        embed.description = description_text
        embed.set_footer(text="EchoVerse Statistik • Daten werden live aktualisiert")
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------
    # Befehl: Wort entfernen
    # ------------------------------------------------------------
    @app_commands.command(
        name="counter_remove", 
        description="Entfernt ein Wort und dessen Statistik aus dem Counter"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def counter_remove(self, interaction: discord.Interaction, wort: str):
        word_clean = wort.strip().lower()
        
        if db_counter.delete_counter(str(interaction.guild_id), word_clean):
            await interaction.response.send_message(
                f"🗑️ Der Counter für `{word_clean}` wurde erfolgreich gelöscht.", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Das Wort `{word_clean}` konnte nicht in der Datenbank gefunden werden.", 
                ephemeral=True
            )

    # ------------------------------------------------------------
    # Befehl: Counter zurücksetzen (auf 0 setzen)
    # ------------------------------------------------------------
    @app_commands.command(
        name="counter_reset", 
        description="Setzt den Zähler eines Wortes auf 0 zurück"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def counter_reset(self, interaction: discord.Interaction, wort: str):
        word_clean = wort.strip().lower()
        
        if db_counter.reset_counter(str(interaction.guild_id), word_clean):
            await interaction.response.send_message(
                f"🔄 Der Zähler für `{word_clean}` wurde auf 0 zurückgesetzt.", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Fehler: `{word_clean}` wird momentan nicht gezählt.", 
                ephemeral=True
            )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Counter(bot))