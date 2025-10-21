import discord
from discord.ext import commands
from discord import app_commands
import time
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.util import ClassNotFound

class CodeExtractor(commands.Cog):
    """Cog für Message Context Menu 'toCode'"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------
    # Context Menu Command registrieren
    # ------------------------------------------------------------
    @app_commands.context_menu(name="toCode")
    async def to_code(self, interaction: discord.Interaction, message: discord.Message):
        start_time = time.perf_counter()

        content = message.content
        if not content:
            await interaction.response.send_message(
                "❌ Diese Nachricht enthält keinen Text.", ephemeral=True
            )
            return

        # --------------------------------------------------------
        # Sprache ermitteln
        # --------------------------------------------------------
        try:
            lexer = guess_lexer(content)
            language = lexer.name.lower()  # z.B. python, javascript, etc.
        except ClassNotFound:
            language = ""  # Kein spezieller Codeblock, normale Markdown
        end_time = time.perf_counter()
        duration = end_time - start_time

        # --------------------------------------------------------
        # Nachricht als Codeblock zurückgeben
        # --------------------------------------------------------
        code_block = f"```{language}\n{content}\n```" if language else f"```\n{content}\n```"

        embed = discord.Embed(
            title="💻 Nachricht als Code",
            description=code_block,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"-# Ermittlung der Sprache hat {duration:.2f} Sekunden gedauert")

        await interaction.response.send_message(embed=embed)

# ------------------------------------------------------------
# Cog Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(CodeExtractor(bot))
