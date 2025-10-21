# cogs/help.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional

class Help(commands.Cog):
    """Bietet Hilfe zu den verfügbaren Modulen und Befehlen"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Füllen der Cog-Namen Liste hier ist nicht nötig, da wir sie bei jeder Ausführung neu erstellen,
        # was dynamischer ist, falls Cogs nach dem Start geladen werden.

# ------------------------------------------------------------
# Help Befehle
# ------------------------------------------------------------

    @commands.hybrid_command(
        name="help",
        description="Zeigt alle verfügbaren Module oder die Befehle eines Moduls an."
    )
    async def help(
        self,
        ctx: Context[commands.Bot],
        category: Optional[str] = None
    ) -> None:
        category = category.lower() if category else None
        embed = discord.Embed(color=discord.Color.blue())

        # ------------------------------------------------------------
        # 1. Keine Kategorie angegeben: Liste alle Cogs auf
        # ------------------------------------------------------------
        if category is None:
            
            # Sammle alle Cog-Namen und ihre Beschreibungen
            all_cogs = {}
            for cog_name, cog in self.bot.cogs.items():
                if cog_name == "Help":
                    continue  # Überspringe das Help-Cog selbst
                
                # Verwende die Docstring des Cogs als Beschreibung
                description = cog.__doc__.strip() if cog.__doc__ else "Keine Beschreibung verfügbar."
                all_cogs[cog_name.lower()] = description

            cog_list_str = "\n".join(
                [f"• **{name.capitalize()}** – {desc}" for name, desc in all_cogs.items()]
            )

            embed.title = "Hilfe – Verfügbare Module (Cogs)"
            embed.description = (
                f"Verwende `/help <modulname>` für Details zu einem spezifischen Modul.\n\n"
                f"{cog_list_str}"
            )
            
        # ------------------------------------------------------------
        # 2. Kategorie (Cog-Name) angegeben: Zeige Befehle des Cogs an
        # ------------------------------------------------------------
        else:
            # 💡 KORREKTUR: Finde den tatsächlichen Cog-Namen (korrekte Groß-/Kleinschreibung)
            cog_name_actual = next((c for c in self.bot.cogs if c.lower() == category), None)
            
            if cog_name_actual:
                cog = self.bot.get_cog(cog_name_actual)
            
                if not cog:
                    # Sollte hier nicht mehr passieren, aber zur Sicherheit beibehalten
                    embed.title = "Unbekanntes Modul"
                    embed.description = f"Das Modul **{category}** konnte nicht gefunden werden."
                    embed.color = discord.Color.red()
                else:
                    embed.title = f"Befehle im Modul: {cog_name_actual}"
                    
                    # Verwende walk_commands(), um alle Befehle und Unterbefehle rekursiv zu finden
                    commands_in_cog = []
                    for cmd in cog.walk_commands():
                        if cmd.name != 'help': 
                            commands_in_cog.append(cmd)
                    
                    if not commands_in_cog:
                        embed.description = "Dieses Modul enthält keine registrierten Befehle."
                    else:
                        for cmd in commands_in_cog:
                            # Verwende qualified_name für Gruppenbefehle (z.B. quiz add)
                            full_command_name = f"/{cmd.qualified_name}"
                            
                            # Verwende die Beschreibung des Befehls (aus `description` oder `help`)
                            description = cmd.description if cmd.description else cmd.help or "Keine Beschreibung"
                            
                            embed.add_field(
                                name=full_command_name,
                                value=description,
                                inline=False
                            )

            # ------------------------------------------------------------
            # 3. Unbekannte Kategorie
            # ------------------------------------------------------------
            else:
                embed.title = "Unbekanntes Modul"
                embed.description = "Verwende `/help` ohne Argumente, um alle verfügbaren Module anzuzeigen."
                embed.color = discord.Color.red()

        # Antwort senden
        if ctx.interaction:
            await ctx.reply(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    # WICHTIG: Ersetze den Standard-Help-Befehl
    bot.remove_command("help")
    await bot.add_cog(Help(bot))