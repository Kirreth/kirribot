import discord
from discord.ext import commands
import os

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))

class WelcomeLeave(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invites = {}  # Stores invites per guild

    @commands.Cog.listener()
    async def on_ready(self):
        # Alle Einladungen pro Guild beim Start speichern
        for guild in self.bot.guilds:
            self.invites[guild.id] = await guild.invites()
        print("✅ WelcomeLeave Cog bereit!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = guild.get_channel(WELCOME_CHANNEL_ID)

        if not channel:
            return  # Kein Channel gesetzt oder falsche ID

        # Neue Einladungen abrufen und vergleichen
        new_invites = await guild.invites()
        used_invite = None
        for invite in new_invites:
            for old_invite in self.invites.get(guild.id, []):
                if invite.code == old_invite.code and invite.uses > old_invite.uses:
                    used_invite = invite
                    break

        self.invites[guild.id] = new_invites  # Update invites

        embed = discord.Embed(
            title="👋 Neuer Server-Mitglied",
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

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        channel = guild.get_channel(WELCOME_CHANNEL_ID)

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
