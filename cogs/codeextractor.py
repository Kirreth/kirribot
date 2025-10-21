import discord
from discord.ext import commands
from discord import app_commands
import time
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.util import ClassNotFound

# ------------------------------------------------------------
# Context Menu Command auf Modulebene
# ------------------------------------------------------------
async def to_code_callback(interaction: discord.Interaction, message: discord.Message):
    start_time = time.perf_counter()

    content = message.content
    if not content:
        await interaction.response.send_message(
            "❌ Diese Nachricht enthält keinen Text.", ephemeral=True
        )
        return

    # --------------------------------------------------------
    # Sprache ermitteln (robuster)
    # --------------------------------------------------------
    language = ""
    try:
        # Versuch, den Lexer anhand des Inhalts zu erraten
        lexer = guess_lexer(content)
        language = lexer.name.lower()
    except ClassNotFound:
        language = ""  # kein spezieller Codeblock

    end_time = time.perf_counter()
    duration = end_time - start_time

    # --------------------------------------------------------
    # Nachricht mit Codeblock + Dauer
    # --------------------------------------------------------
    formatted_message = f"```{language}\n{content}\n```\n-# Ermittlung der Sprache hat {duration:.2f} Sekunden gedauert"

    await interaction.response.send_message(formatted_message)

# ------------------------------------------------------------
# Cog für andere Befehle (falls benötigt)
# ------------------------------------------------------------
class CodeExtractor(commands.Cog):
    """Cog für zusätzliche Commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

# ------------------------------------------------------------
# Cog Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(CodeExtractor(bot))
    # Context Menu auf Bot-Tree registrieren
    bot.tree.add_command(app_commands.ContextMenu(
        name="toCode",
        callback=to_code_callback
    ))
