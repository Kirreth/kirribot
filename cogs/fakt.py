import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
from datetime import datetime, time, timedelta

FACT_FILE = "data/fakten.json"
CHANNEL_ID = 1429882849334530192

# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------
def ensure_fact_file():
    os.makedirs(os.path.dirname(FACT_FILE), exist_ok=True)
    if not os.path.exists(FACT_FILE):
        with open(FACT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

def load_facts():
    ensure_fact_file()
    with open(FACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_facts(facts):
    ensure_fact_file()
    with open(FACT_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=4, ensure_ascii=False)

# ------------------------------------------------------------
# Cog
# ------------------------------------------------------------
class Fakt(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_fact.start()

    def cog_unload(self):
        self.daily_fact.cancel()

    # ------------------------------------------------------------
    # /fakt Command
    # ------------------------------------------------------------
    @commands.hybrid_command(name="fakt", description="Füge einen Fakt hinzu (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_fact(self, ctx: commands.Context, *, content: str):
        facts = load_facts()
        facts.append(content)
        save_facts(facts)
        await ctx.send(f"✅ Fakt hinzugefügt: {content}", ephemeral=True)

    # ------------------------------------------------------------
    # Täglicher Task
    # ------------------------------------------------------------
    @tasks.loop(hours=24)
    async def daily_fact(self):
        await self.bot.wait_until_ready()
        facts = load_facts()
        if not facts:
            return  # Kein Fakt vorhanden, nichts posten

        # Optional: zufälligen Fakt nehmen
        fact = facts[0]

        channel = self.bot.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="📌 Fakt des Tages",
                description=fact,
                color=discord.Color.green()
            )
            await channel.send(embed=embed)

    @daily_fact.before_loop
    async def before_daily_fact(self):
        await self.bot.wait_until_ready()
        now = datetime.utcnow()
        target = datetime.combine(now.date(), time(hour=20))  # 20 Uhr UTC
        if now > target:
            target += timedelta(days=1)
        await discord.utils.sleep_until(target)

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Fakt(bot))
