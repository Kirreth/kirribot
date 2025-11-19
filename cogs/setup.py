# cogs/setup.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
from utils.database import birthday as birthday_db
from utils.database import moderation as mod_db
from utils.database import roles as roles_db
from utils.database import bumps as db_bumps
from utils.database import guilds as db_guilds

class Setup(commands.Cog):
    """Zentrale Oberfläche für die Konfiguration von Channels und Rollen."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    # ------------------------------------------------------------
    # Cog-weit: Nur Moderatoren/Admins dürfen Commands ausführen
    # ------------------------------------------------------------
    async def cog_check(self, ctx: Context):
        if not ctx.guild:
            # Fehlerbehandlung für DMs
            await ctx.send("❌ Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)
            return False
            
        perms = ctx.author.guild_permissions
        
        # Prüfung auf Administrator ODER Server verwalten
        if perms.administrator or perms.manage_guild:
            return True
        else:
            # Benutzerdefinierte Rückmeldung bei fehlender Berechtigung
            await ctx.send(
                "❌ **Zugriff verweigert.** Diese Funktion steht nur **Administratoren** oder Nutzern mit der Berechtigung **'Server verwalten'** zur Verfügung.", 
                ephemeral=True
            )
            return False

    # ------------------------------------------------------------
    # Hauptbefehlsgruppe
    # ------------------------------------------------------------
    
    @commands.hybrid_group(
        name="setup", 
        description="Konfiguriere alle wichtigen Channel und Rollen des Bots."
    )
    @commands.guild_only() 
    @commands.has_permissions(administrator=True) # Der cog_check greift zuerst und liefert die Fehlermeldung
    async def setup(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⚙️ Bot-Konfiguration",
                description=(
                    "Bitte verwende einen Unterbefehl:\n\n"
                    "• `/setup channel` - Konfiguriert Channels (Birthday, Sanctions, Posts)\n"
                    "• `/setup role` - Konfiguriert spezielle Rollen (Bumper-Rolle)"
                ),
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------
    # Prefix / Serverweite Einstellungen
    # ------------------------------------------------------------
    @setup.group(
        name="serversettings",
        description="Konfiguriert serverweite Einstellungen wie den Bot-Prefix."
    )
    async def setup_serversettings(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende einen Unterbefehl: `/setup serversettings prefix`", ephemeral=True)

    @setup_serversettings.command(
        name="prefix",
        description="Ändert den Bot-Prefix für diesen Server."
    )
    async def set_prefix(self, ctx: Context, prefix: str):
        guild_id = str(ctx.guild.id)
        
        if len(prefix) > 5:
            await ctx.send("❌ Der Prefix darf höchstens 5 Zeichen lang sein.", ephemeral=True)
            return
            
        try:
            db_guilds.set_prefix(guild_id, prefix) 
            await ctx.send(f"✅ Prefix wurde auf `{prefix}` geändert!", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Fehler beim Speichern des Prefix: {e}", ephemeral=True)

    # ------------------------------------------------------------
    # Channels
    # ------------------------------------------------------------
    @setup.group(
        name="channel", 
        description="Konfiguriert Channels für Geburtstage, Moderation und Posts."
    )
    async def setup_channel(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende `/setup channel <birthday/sanctions/voice/checkpost/post/reminder/joinleft>`", ephemeral=True)

    # Birthday-Channel
    @setup_channel.command(
        name="birthday",
        description="Setzt den Channel für Geburtstagsnachrichten."
    )
    async def channel_birthday(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        if channel is None:
            db_guilds.set_birthday_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Der Geburtstags-Channel wurde entfernt.", ephemeral=True)
        else:
            db_guilds.set_birthday_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Geburtstags-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # Sanctions-Channel
    @setup_channel.command(
        name="sanctions",
        description="Setzt den Channel für Sanctions/Mod-Logs."
    )
    async def channel_sanctions(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        if channel is None:
            db_guilds.set_sanctions_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Der Sanctions-Channel wurde entfernt.", ephemeral=True)
        else:
            db_guilds.set_sanctions_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Sanctions-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # Bump-Reminder-Channel
    @setup_channel.command(
        name="reminder",
        description="Setzt den Channel für Bump-Erinnerungen."
    )
    async def channel_reminder(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        if channel is None:
            db_guilds.set_bump_reminder_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Bump-Reminder-Channel entfernt.", ephemeral=True)
        else:
            db_guilds.set_bump_reminder_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Bump-Reminder-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # Join/Leave-Channel
    @setup_channel.command(
        name="joinleft",
        description="Setzt den Channel, in dem Join- und Leave-Nachrichten gepostet werden."
    )
    async def channel_joinleft(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        from utils.database import joinleft as db_joinleft

        guild_id = str(ctx.guild.id)
        if channel is None:
            db_joinleft.set_welcome_channel(guild_id, None)
            await ctx.send("✅ Der Join/Leave-Channel wurde entfernt.", ephemeral=True)
        else:
            db_joinleft.set_welcome_channel(guild_id, str(channel.id))
            await ctx.send(f"✅ Join/Leave-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # Voice-Channel
    @setup_channel.command(
        name="voice",
        description="Setzt den 'Join-to-Create' Starter-Channel für dynamische Sprachkanäle."
    )
    async def channel_voice(self, ctx: Context, channel: Union[discord.VoiceChannel, None]) -> None:
        guild_id = str(ctx.guild.id)
        if channel is None:
            db_guilds.set_dynamic_voice_channel(guild_id, None) 
            await ctx.send("✅ Der 'Join-to-Create' Starter-Channel wurde entfernt.", ephemeral=True)
        else:
            db_guilds.set_dynamic_voice_channel(guild_id, str(channel.id))
            await ctx.send(
                f"✅ 'Join-to-Create' Starter-Channel gesetzt auf {channel.mention}.",
                ephemeral=True
            )

    # -----------------------------
    # Post-System Channels
    # -----------------------------
    @setup_channel.command(
        name="checkpost",
        description="Setzt den Channel für eingereichte Posts, die geprüft werden."
    )
    async def channel_checkpost(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        guild_id = str(ctx.guild.id)
        if channel is None:
            db_guilds.set_checkpost_channel(guild_id, None)
            await ctx.send("✅ Checkpost-Channel wurde entfernt.", ephemeral=True)
        else:
            db_guilds.set_checkpost_channel(guild_id, str(channel.id))
            await ctx.send(f"✅ Checkpost-Channel gesetzt auf {channel.mention}", ephemeral=True)

    @setup_channel.command(
        name="post",
        description="Setzt den Channel für genehmigte Posts."
    )
    async def channel_post(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        guild_id = str(ctx.guild.id)
        if channel is None:
            db_guilds.set_post_channel(guild_id, None)
            await ctx.send("✅ Post-Channel wurde entfernt.", ephemeral=True)
        else:
            db_guilds.set_post_channel(guild_id, str(channel.id))
            await ctx.send(f"✅ Post-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # ------------------------------------------------------------
    # Rollen
    # ------------------------------------------------------------
    @setup.group(
        name="role",
        description="Konfiguriert Rollen wie die Bumper-Rolle."
    )
    async def setup_role(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende `/setup role <bumper>`", ephemeral=True)

    @setup_role.command(
        name="bumper",
        description="Setzt die Rolle, die nach einem Bump vergeben wird."
    )
    async def role_bumper(self, ctx: Context, role: Union[discord.Role, None]) -> None:
        if role is None:
            db_guilds.set_bumper_role(str(ctx.guild.id), None)
            await ctx.send("✅ Bumper-Rolle entfernt.", ephemeral=True)
        else:
            db_guilds.set_bumper_role(str(ctx.guild.id), str(role.id))
            await ctx.send(f"✅ Bumper-Rolle gesetzt auf {role.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Setup(bot))