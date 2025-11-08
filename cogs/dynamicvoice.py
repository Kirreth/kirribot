import discord
from discord.ext import commands
from utils.database import guilds as db_guilds

class DynamicVoice(commands.Cog):
    """Erstellt dynamische Voice Channels beim Beitritt in einen speziellen 'Join to Create' Kanal."""
    def __init__(self, bot):
        self.bot = bot
        
        self.temp_channels = set()


    # ------------------------------------------------------------------
    # HELFERMETHODE: Erstellt den neuen Starter Channel
    # ------------------------------------------------------------------
    async def _recreate_starter_channel(self, guild: discord.Guild, category: discord.CategoryChannel):
        """Erstellt den neuen Starter-Channel und speichert dessen ID."""
        new_channel = await guild.create_voice_channel(
            name="➕ | Join to Create", 
            category=category,
            position=0
        )
        
        db_guilds.set_dynamic_voice_channel(str(guild.id), str(new_channel.id))
        print(f"✅ Neuer Starter-Channel erstellt: {new_channel.name} ({new_channel.id}) in {guild.name}")
        return new_channel


    # ------------------------------------------------------------------
    # Bot-Start-Check
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        """Überprüft beim Start, ob der Starter-Channel für jeden Server existiert und gültig ist."""
        await self.bot.wait_until_ready()
        
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            starter_channel_id_str = db_guilds.get_dynamic_voice_channel(guild_id)
            
            if starter_channel_id_str:
                try:
                    starter_channel_id = int(starter_channel_id_str)
                    current_channel = self.bot.get_channel(starter_channel_id)
                except ValueError:
                    current_channel = None
                
                if not current_channel or not isinstance(current_channel, discord.VoiceChannel):
                    print(f"WARNUNG: Starter-Channel für '{guild.name}' (ID {starter_channel_id_str}) fehlt oder ist ungültig. Setze auf None.")
                    db_guilds.set_dynamic_voice_channel(guild_id, None)
                    print(f"HINWEIS: Bitte setzen Sie den Dynamic Voice Channel für '{guild.name}' neu mit /setup channel voice.")


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild_id = str(member.guild.id)
        
        starter_channel_id_str = db_guilds.get_dynamic_voice_channel(guild_id)
        
        if not starter_channel_id_str:
            return
        try:
            STARTER_CHANNEL_ID = int(starter_channel_id_str)
        except (TypeError, ValueError):
            return 
        
        # ----------------------------------
        # A. KANAL ERSTELLEN (Join to Create)
        # ----------------------------------
        if after.channel and after.channel.id == STARTER_CHANNEL_ID:
            
            guild = member.guild
            category = after.channel.category
            
            new_name = f"🔊 {member.display_name}'s Voice"
            
            
            new_channel = await guild.create_voice_channel(
                name=new_name, 
                category=category,
            )
            
            await member.move_to(new_channel)
            
            self.temp_channels.add(new_channel.id)

        # ----------------------------------
        # B. LÖSCHEN DER TEMPORÄREN KANÄLE 
        # ----------------------------------
        if before.channel and before.channel.id in self.temp_channels:
            channel_to_check = before.channel
            
            if len(channel_to_check.members) == 0:
                try:
                    await channel_to_check.delete()
                    self.temp_channels.remove(channel_to_check.id)
                    print(f"✅ Temporärer VC gelöscht: {channel_to_check.name}")
                except discord.NotFound:
                    pass
                except Exception as e:
                    print(f"Fehler beim Löschen des temporären Voice Channels: {e}")
                        
        # ----------------------------------
        # C. LÖSCHEN UND NEUERSTELLUNG DES STARTER-KANALS
        # ----------------------------------
        if before.channel and before.channel.id == STARTER_CHANNEL_ID:
            channel_to_check = before.channel
            
            if len(channel_to_check.members) == 0:
                try:
                    category = channel_to_check.category
                    
                    await channel_to_check.delete()
                    print(f"✅ Alter Starter-Channel gelöscht: {channel_to_check.name} in {member.guild.name}")

                    await self._recreate_starter_channel(member.guild, category)
                    
                except discord.NotFound:
                    pass
                except Exception as e:
                    print(f"❌ FATALER FEHLER beim Löschen/Neuerstellen des Starter-VC: {e}")
                        
async def setup(bot: commands.Bot) -> None:
    """Setup-Funktion, um das Cog zu laden."""
    await bot.add_cog(DynamicVoice(bot))