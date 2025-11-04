import discord
from discord.ext import commands
from utils.database import joinleft as db_joinleft


class WelcomeLeave(commands.Cog):
    """Loggt Member Join/Leave Ereignisse mit Invite-Tracking"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invites = {}

    # ------------------------------------------------------------
    # Bot ist bereit
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                self.invites[guild.id] = []
        print("✅ WelcomeLeave Cog bereit!")

    # ------------------------------------------------------------
    # Member beitritt
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel_id = db_joinleft.get_welcome_channel(str(guild.id))

        if not channel_id:
            return  # Kein Channel in DB gespeichert

        channel = guild.get_channel(int(channel_id))
        if not channel:
            return  # Channel wurde gelöscht oder ist ungültig

        # ------------------------------------------------------------
        # Invite-Tracking
        # ------------------------------------------------------------
        try:
            new_invites = await guild.invites()
        except discord.Forbidden:
            new_invites = []

        used_invite = None
        for invite in new_invites:
            for old_invite in self.invites.get(guild.id, []):
                if invite.code == old_invite.code and invite.uses > old_invite.uses:
                    used_invite = invite
                    break

        self.invites[guild.id] = new_invites

        embed = discord.Embed(
            title="👋 Neues Mitglied ist beigetreten!",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=member.mention, inline=True)

        if used_invite:
            embed.add_field(
                name="Eingeladen von",
                value=f"{used_invite.inviter.mention} ({used_invite.code})",
                inline=True
            )

        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

    # ------------------------------------------------------------
    # Member verlässt den Server
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        channel_id = db_joinleft.get_welcome_channel(str(guild.id))

        if not channel_id:
            return  # Kein Channel gespeichert

        channel = guild.get_channel(int(channel_id))
        if not channel:
            return

        embed = discord.Embed(
            title="👋 Mitglied hat den Server verlassen",
            description=f"{member.name} ({member.id})",
            color=discord.Color.red()
        )

        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeLeave(bot))
