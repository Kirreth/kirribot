import discord
from discord.ext import commands

class WelcomeLeave(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invites = {}  # Stores invites per guild

    @commands.Cog.listener()
    async def on_ready(self):
        # Alle Einladungen pro Guild beim Start speichern
        for guild in self.bot.guilds:
            self.invites[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = discord.utils.get(guild.text_channels, name="welcome")  # Channelname anpassen

        # Neue Einladungen abrufen und vergleichen
        new_invites = await guild.invites()
        used_invite = None
        for invite in new_invites:
            for old_invite in self.invites.get(guild.id, []):
                if invite.code == old_invite.code and invite.uses > old_invite.uses:
                    used_invite = invite
                    break

        self.invites[guild.id] = new_invites  # Update invites

        if channel:
            msg = f"👋 {member.mention} ist dem Server beigetreten!"
            if used_invite:
                msg += f" Über Einladung von {used_invite.inviter.mention} ({used_invite.code})."
            await channel.send(msg)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        channel = discord.utils.get(guild.text_channels, name="welcome")  # Gleiches Channel
        if channel:
            await channel.send(f"👋 {member.name} hat den Server verlassen.")

async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeLeave(bot))
