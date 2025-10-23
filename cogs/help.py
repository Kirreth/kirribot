# cogs/help.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional

class Help(commands.Cog):
    """Bietet Hilfe zu den verfügbaren Modulen und Befehlen"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        # Sicherstellen, dass die Verarbeitung nur auf Servern erfolgt, wo es sinnvoll ist
        if ctx.guild is None and category is None:
            # Einfache Fallback-Meldung für DMs ohne Argument
            await ctx.send("Bitte verwende diesen Befehl in einem Server, um verfügbare Module zu sehen, oder gib den Namen eines Moduls an, falls du ihn kennst.")
            return

        category = category.lower() if category else None
        embed = discord.Embed(color=discord.Color.blue())

        # ------------------------------------------------------------
        # 1. Keine Kategorie angegeben: Liste alle Cogs auf
        # ------------------------------------------------------------
        if category is None:
            
            all_cogs = {}
            for cog_name, cog in self.bot.cogs.items():
                # 🚩 VERBESSERUNG: Überspringe das Help-Cog und Cogs, deren Namen mit Unterstrich beginnen (interne Cogs)
                if cog_name == "Help" or cog_name.startswith('_'): 
                    continue
                
                # Verwende die Docstring des Cogs als Beschreibung
                description = cog.__doc__.strip() if cog.__doc__ else "Keine Beschreibung verfügbar."
                all_cogs[cog_name.capitalize()] = description # Verwende capitalize() hier für die Anzeige

            cog_list_str = "\n".join(
                [f"• **{name}** – {desc}" for name, desc in all_cogs.items()]
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
            # Finde den tatsächlichen Cog-Namen (korrekte Groß-/Kleinschreibung)
            cog_name_actual = next((c for c in self.bot.cogs if c.lower() == category), None)
            
            if cog_name_actual:
                cog = self.bot.get_cog(cog_name_actual)
            
                if not cog:
                    # Sollte hier nicht mehr passieren
                    pass 
                else:
                    embed.title = f"Befehle im Modul: {cog_name_actual}"
                    embed.description = cog.__doc__.strip() if cog.__doc__ else "Keine Beschreibung verfügbar."
                    
                    commands_in_cog = []
                    # Verwende walk_commands(), um alle Befehle und Unterbefehle rekursiv zu finden
                    for cmd in cog.walk_commands():
                        # 🚩 VERBESSERUNG: Überspringe versteckte Befehle und den Help-Befehl selbst
                        if cmd.name != 'help' and not cmd.hidden: 
                            commands_in_cog.append(cmd)
                    
                    if not commands_in_cog:
                        if len(embed.description) < 50:
                             embed.description += "\n\nDieses Modul enthält keine sichtbaren Befehle."
                        else:
                             embed.description = "Dieses Modul enthält keine sichtbaren Befehle."
                    else:
                        for cmd in commands_in_cog:
                            # Verwende qualified_name für Gruppenbefehle (z.B. quiz add)
                            full_command_name = f"/{cmd.qualified_name}"
                            
                            # Verwende die Beschreibung des Befehls (aus `description` oder `help`)
                            description = cmd.description if cmd.description else cmd.help or "Keine Beschreibung"
                            
                            # Entferne unnötige Leerzeichen
                            description = description.strip()
                            
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

        # Antwort senden (Hybrid Command Logik)
        # Sende ephemeral (privat) bei Slash Commands, öffentlich bei Prefix Commands
        ephemeral_status = ctx.interaction is not None
        await ctx.send(embed=embed, ephemeral=ephemeral_status)


async def setup(bot: commands.Bot) -> None:
    # WICHTIG: Ersetze den Standard-Help-Befehl
    bot.remove_command("help")
    await bot.add_cog(Help(bot))