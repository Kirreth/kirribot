import discord
from discord.ext import commands
from discord import app_commands, ui
import aiohttp
from typing import Dict, Any

# ------------------------------------------------------------
# Context Menu Callback Funktion
# ------------------------------------------------------------
async def convertToOthers(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=False, thinking=True)

    content = message.content.strip()
    
    if not content:
        await interaction.followup.send(
            "❌ Diese Nachricht enthält keinen Text.", ephemeral=True
        )
        return

    original_url = content.split()[0]
    
    api_url = "https://api.song.link/v1-alpha.1/links"
    params = {'url': original_url}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, params=params) as response:
                
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get('message', f"Unbekannter API-Fehler ({response.status})")
                    await interaction.followup.send(
                        f"❌ Fehler bei der API-Anfrage: {error_message}", ephemeral=True
                    )
                    return
                
                data: Dict[str, Any] = await response.json()
                
        except aiohttp.ClientConnectorError:
            await interaction.followup.send(
                "❌ Konnte keine Verbindung zum Konverter-Dienst herstellen.", ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}", ephemeral=True
            )
            return

    # Daten und Links extrahieren
    links_by_platform: Dict[str, Dict[str, Any]] = data.get('linksByPlatform', {})
    
    platform_map = {
        'spotify': {"label": "Spotify", "emoji": "🟢"},
        'youtube': {"label": "YouTube Music", "emoji": "🔴"},
        'appleMusic': {"label": "Apple Music", "emoji": "🍎"},
        'deezer': {"label": "Deezer", "emoji": "⚫"},
    }
    
    # Erstelle Buttons
    view = ui.View()
    found_links_count = 0

    for platform_key, info in platform_map.items():
        platform_object = links_by_platform.get(platform_key, {}) 
        link = platform_object.get('url')
        if link:
            button = ui.Button(
                label=info['label'],
                style=discord.ButtonStyle.link,
                url=link,
                emoji=info['emoji']
            )
            view.add_item(button)
            found_links_count += 1
    
    
    # -------------------------------------------------------------------
    # NEUE, ROBUSTE METADATEN-EXTRAKTION (mit Fallback)
    # -------------------------------------------------------------------
    entities_by_id: Dict[str, Dict[str, Any]] = data.get('entitiesByUniqueId', {})
    entity_unique_id = data.get('entityUniqueId')
    
    title = ""
    artist = ""
    thumbnail_url = ""

    if entity_unique_id and entity_unique_id in entities_by_id:
        central_entity = entities_by_id[entity_unique_id]
        title = central_entity.get('title', "")
        artist = central_entity.get('artistName', "")
        thumbnail_url = central_entity.get('thumbnailUrl', "")

    for entity_id, entity_data in entities_by_id.items():
        
        if not title or title == "Unbekannter Titel":
            title = entity_data.get('title', title)
        
        if not artist or artist == "Unbekannter Künstler":
            artist = entity_data.get('artistName', artist)
        
        if not thumbnail_url:
            thumbnail_url = entity_data.get('thumbnailUrl', thumbnail_url)
        
        if title and artist and title != "Unbekannter Titel" and artist != "Unbekannter Künstler":
            break

    title = title if title and title != "Unbekannter Titel" else "Unbekannter Titel"
    artist = artist if artist else "Unbekannter Künstler"
    # -------------------------------------------------------------------

    
    if found_links_count == 0:
        await interaction.followup.send(
            "❌ Es konnten keine konvertierten Links gefunden werden. Prüfe, ob es ein gültiger Song-Link ist.", ephemeral=True
        )
        return
    
    
    embed = discord.Embed(
        title=f"🎶 {title} von {artist}",
        description="**Wähle deine Streaming-Plattform:**",
        color=discord.Color.blue()
    )
    
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
        
    
    await interaction.followup.send(embed=embed, view=view)


# ------------------------------------------------------------
# Cog für andere Befehle
# ------------------------------------------------------------
class MusicConverter(commands.Cog):
    """Cog für die Musiklink-Konvertierung als Context Menu Command"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

# ------------------------------------------------------------
# Cog Setup 
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(MusicConverter(bot))
    
    bot.tree.add_command(app_commands.ContextMenu(
        name="Link konvertieren",
        callback=convertToOthers
    ))