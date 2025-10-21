import discord
from discord.ext import commands
from utils.database import connection as db
from datetime import datetime

class SelfInfo(commands.Cog):
    """Zeigt alle gespeicherten Infos über den Nutzer."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="selfinfo", description="Zeigt alle gespeicherten Infos über dich.")
    async def selfinfo(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)

        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # ------------------------------------------------------------
        # LEVELDATEN
        # ------------------------------------------------------------
        cursor.execute("""
            SELECT level, counter 
            FROM user 
            WHERE id = %s
        """, (user_id,))
        level_data = cursor.fetchone()

        # ------------------------------------------------------------
        # GEBURTSTAG
        # ------------------------------------------------------------
        cursor.execute("""
            SELECT birthday 
            FROM birthdays 
            WHERE user_id = %s AND guild_id = %s
        """, (user_id, guild_id))
        birthday_data = cursor.fetchone()

        # ------------------------------------------------------------
        # VERWARNUNGEN
        # ------------------------------------------------------------
        cursor.execute("""
            SELECT COUNT(*) AS count 
            FROM warns 
            WHERE user_id = %s AND guild_id = %s
        """, (user_id, guild_id))
        warn_data = cursor.fetchone()

        # ------------------------------------------------------------
        # QUIZ
        # ------------------------------------------------------------
        cursor.execute("""
            SELECT score, date_played 
            FROM quiz_results 
            WHERE user_id = %s AND guild_id = %s
        """, (user_id, guild_id))
        quiz_data = cursor.fetchone()

        cursor.close()
        conn.close()

        # ------------------------------------------------------------
        # EMBED
        # ------------------------------------------------------------
        embed = discord.Embed(
            title=f"📋 Gespeicherte Daten von {ctx.author.display_name}",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar)

        # Levelsystem
        if level_data:
            embed.add_field(
                name="🏆 Levelsystem",
                value=f"Level: **{level_data['level']}**\nXP: **{level_data['counter']}**",
                inline=False
            )
        else:
            embed.add_field(name="🏆 Levelsystem", value="Keine Daten gefunden.", inline=False)

        # Geburtstag
        if birthday_data:
            embed.add_field(
                name="🎂 Geburtstag",
                value=f"{birthday_data['birthday']}",
                inline=False
            )
        else:
            embed.add_field(name="🎂 Geburtstag", value="Kein Geburtstag gespeichert.", inline=False)

        # Verwarnungen
        if warn_data and warn_data["count"] > 0:
            embed.add_field(
                name="⚠️ Verwarnungen",
                value=f"{warn_data['count']} Verwarnung(en)",
                inline=False
            )
        else:
            embed.add_field(name="⚠️ Verwarnungen", value="Keine Verwarnungen.", inline=False)

        # Quiz-Ergebnisse
        if quiz_data:
            embed.add_field(
                name="🧠 Quiz",
                value=f"Punkte: **{quiz_data['score']}**\nDatum: {quiz_data['date_played']}",
                inline=False
            )
        else:
            embed.add_field(name="🧠 Quiz", value="Noch kein Quiz gespielt.", inline=False)

        embed.set_footer(text="Datenauszug aus der internen Bot-Datenbank")

        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SelfInfo(bot))
