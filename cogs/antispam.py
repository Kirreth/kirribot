import discord
from discord.ext import commands
from datetime import timedelta
from collections import defaultdict, deque
import time

from utils.database import guilds as db_guilds

# ------------------------------------------------------------
# Button View
# ------------------------------------------------------------
class SpamActionView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @discord.ui.button(label="🔨 Bannen", style=discord.ButtonStyle.danger)
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.ban(reason="Spam erkannt (Antispam-System)")
            await interaction.response.send_message("User wurde gebannt.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)

    @discord.ui.button(label="✅ Freigeben", style=discord.ButtonStyle.success)
    async def release(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.timeout(None)
            await interaction.response.send_message("Timeout wurde aufgehoben.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)


# ------------------------------------------------------------
# Antispam Cog
# ------------------------------------------------------------
class AntiSpam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # user_id -> deque[(message_content, timestamp, message)]
        self.message_cache = defaultdict(lambda: deque(maxlen=10))

        self.mod_channels = {}

    async def cog_load(self):
        for guild in self.bot.guilds:
            channel_id = db_guilds.get_sanctions_channel(str(guild.id))
            if channel_id:
                self.mod_channels[guild.id] = int(channel_id)

    # ------------------------------------------------------------
    # Message Listener
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        member = message.author

        # Mods/Admins ignorieren
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return

        now = time.time()

        cache = self.message_cache[member.id]
        cache.append((message.content, now, message))

        # Filter: nur gleiche Nachrichten in letzten 2 Sekunden
        recent = [m for m in cache if now - m[1] <= 2]

        if len(recent) < 3:
            return

        contents = [m[0] for m in recent]

        # Prüfen ob alle identisch
        if len(set(contents)) != 1:
            return

        # ------------------------------
        # SPAM ERKANNT
        # ------------------------------
        try:
            # Nachrichten löschen
            for _, _, msg in recent:
                try:
                    await msg.delete()
                except:
                    pass

            # Timeout setzen (24h)
            until = discord.utils.utcnow() + timedelta(hours=24)
            await member.timeout(until, reason="Spam erkannt (3 gleiche Nachrichten)")

        except discord.Forbidden:
            return

        # Cache leeren, damit es nicht mehrfach triggert
        self.message_cache[member.id].clear()

        # ------------------------------
        # Mod-Channel Nachricht
        # ------------------------------
        mod_channel_id = self.mod_channels.get(message.guild.id)
        if not mod_channel_id:
            return

        mod_channel = message.guild.get_channel(mod_channel_id)
        if not mod_channel:
            return

        embed = discord.Embed(
            title="🚨 Spam erkannt",
            description=(
                f"**User:** {member.mention}\n"
                f"**ID:** {member.id}\n\n"
                f"**Nachricht:**\n```{message.content}```\n\n"
                f"➡️ User wurde für 24h in Timeout gesetzt."
            ),
            color=discord.Color.red()
        )

        embed.set_footer(text="Antispam-System")

        view = SpamActionView(member)

        await mod_channel.send(embed=embed, view=view)


# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))