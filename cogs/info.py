# cogs/info.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional
from datetime import datetime
from utils import database as db

class Info(commands.Cog):
    """Bietet Informationen über Benutzer"""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

# ------------------------------------------------------------
# Info über User
# ------------------------------------------------------------
#-------------
# User Info anzeigen
#-------------
    @commands.hybrid_command(
        name="userinfo",
        description="Zeigt Infos über einen Benutzer"
    )
    async def userinfo(self, ctx: Context[commands.Bot], user: discord.Member) -> None:
        
        if ctx.guild is None:
             await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)
             return
             
        embed = discord.Embed(
            title=f"Infos über {user.display_name}", 
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        embed.add_field(name="Name", value=f"{user.display_name} ({user.mention} / `{user.id}`)", inline=False)
        embed.add_field(name="Bot?", value="✅ Ja" if user.bot else "❌ Nein", inline=True)
        embed.add_field(name="Account erstellt", value=user.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)
        if user.joined_at:
            embed.add_field(name="Beigetreten", value=user.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)

# ------------------------------------------------------------
# Rollen des Users
# ------------------------------------------------------------

        roles: list[str] = []
        if ctx.guild:
            default_role = getattr(ctx.guild, "default_role", None)
            sorted_roles = sorted(
                [role for role in user.roles if role != default_role], 
                key=lambda role: role.position, 
                reverse=True
            )
            roles = [role.mention for role in sorted_roles]

        embed.add_field(name="Rollen", value=", ".join(roles) if roles else "Keine Rollen", inline=False)

# ------------------------------------------------------------
# Level des Users
# ------------------------------------------------------------

        guild_id = str(ctx.guild.id)
        user_id = str(user.id)
        conn = db.get_connection()
        
        try:
            cursor = conn.cursor()
            query = "SELECT counter, level FROM user WHERE id = %s AND guild_id = %s"
            cursor.execute(query, (user_id, guild_id)) 
            result = cursor.fetchone()
            cursor.close()

            if result:
                counter, level = result
                embed.add_field(name="Nachrichten", value=f"{counter} Nachrichten", inline=True)
                embed.add_field(name="Level", value=f"🆙 Level {level}", inline=True)
                
        except Exception as e:
            print(f"Fehler bei Datenbankabfrage für Level-Info: {e}")
        finally:
            conn.close()

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))