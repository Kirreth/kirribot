import discord
from discord.ext import commands
from discord import app_commands
import time
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
import re # NEU: Für die Fallback-Mustererkennung

# ------------------------------------------------------------
# Kontext Menü Befehl auf Modulebene (Verbesserte, kostengünstige Version)
# ------------------------------------------------------------
async def to_code_callback(interaction: discord.Interaction, message: discord.Message):
    start_time = time.perf_counter()

    content = message.content.strip() # Whitespace entfernen
    if not content:
        await interaction.response.send_message(
            "❌ Diese Nachricht enthält keinen Text.", ephemeral=True
        )
        return

    # --------------------------------------------------------
    # 1. VERSUCH: Sprache ermitteln mit Pygments (am präzisesten bei viel Code)
    # --------------------------------------------------------
    language = ""
    try:
        # Versuch, den Lexer anhand des Inhalts zu erraten
        lexer = guess_lexer(content)
        language = lexer.name.lower()
    except ClassNotFound:
        language = "" # Pygments konnte die Sprache nicht erraten

    # --------------------------------------------------------
    # 2. FALLBACK: Muster-Matching für kurze, eindeutige Snippets (kostenlos & schnell)
    # --------------------------------------------------------
    if not language:
        # Reguläre Ausdrücke zur Erkennung gängiger Sprachen
        
        # Python: def, class, import, print(), if __name__ ==
        if re.search(r'^\s*(def |class |import |print\s*\(|if __name__ == )', content, re.IGNORECASE | re.MULTILINE):
            language = "python"
        
        # JavaScript/TypeScript/Node: const/let/var, function, console.log
        elif re.search(r'^\s*(const|let|var|function|async function)\s+[\w_]+|^\s*console\.log\(', content):
            language = "javascript" # Standard-Alias
            
        # C/C++/C#/Java (C-ähnlich): #include, public/private/static, int/void/string main
        elif re.search(r'^\s*#include\s+<|^\s*(public|private|static)\s+(void|int|string)\s+(main|class)\s*', content, re.IGNORECASE | re.MULTILINE):
            # Für kurze Snippets ist 'cpp' oder 'c' ein guter, allgemeiner C-Familien-Lexer
            language = "cpp" 

        # SQL: SELECT, INSERT, UPDATE, DELETE, FROM
        elif re.search(r'^\s*(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\s+', content, re.IGNORECASE | re.MULTILINE):
            language = "sql"
            
        # HTML/XML
        elif content.startswith('<') and content.endswith('>'):
            language = "html"


    end_time = time.perf_counter()
    duration = end_time - start_time

    # --------------------------------------------------------
    # Nachricht mit Codeblock + Dauer
    # --------------------------------------------------------
    if not language:
        # Wenn immer noch keine Sprache erkannt, als 'text' oder leer lassen
        language = "text" 

    formatted_message = (
        f"```{language}\n{content}\n```\n"
        f"-# Spracherkennung dauerte {duration:.4f} Sekunden. (Lexer: {language})"
    )

    await interaction.response.send_message(formatted_message)

# ------------------------------------------------------------
# Cog für andere Befehle (falls benötigt)
# ------------------------------------------------------------
class CodeExtractor(commands.Cog):
    """Cog für zusätzliche Commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

# ------------------------------------------------------------
# Cog Setup (unverändert)
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(CodeExtractor(bot))
    # Context Menu auf Bot-Tree registrieren
    bot.tree.add_command(app_commands.ContextMenu(
        name="toCode",
        callback=to_code_callback
    ))