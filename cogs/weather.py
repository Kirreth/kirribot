import os
import httpx
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = os.getenv("WEATHER_API_KEY")

        if not self.api_key:
            print("WARNUNG: API_Key nicht gefunden. Wetterbefehle werden nicht funktionieren.")

    @commands.hybrid_command(
        name="weather",
        description="Zeigt Infos über das Wetter eines Ortes"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def weather(self, ctx: Context, city: str) -> None:
        
        if not self.api_key:
            await ctx.send("Der Wetterdienst ist momentan nicht konfiguriert.", ephemeral=True)
            return

        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "de"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(BASE_URL, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    main_data = data.get("main", {})
                    weather_desc = data["weather"][0]["description"].capitalize()
                    icon_code = data["weather"][0]["icon"]
                    
                    temp = main_data.get("temp")
                    feels_like = main_data.get("feels_like")
                    humidity = main_data.get("humidity")
                    temp_max = main_data.get("temp_max") 
                    temp_min = main_data.get("temp_min") 
                    pressure = main_data.get("pressure") 
                    
                    wind_speed_ms = data.get("wind", {}).get("speed", 0)
                    wind_speed_kmh = wind_speed_ms * 3.6
                    
                    embed = discord.Embed(
                        title=f"Das aktuelle Wetter in {data['name']}, {data['sys']['country']}!",
                        description=f"**{weather_desc}**",
                        color=0x008CB8 
                    )
                    
                    embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon_code}@2x.png")

                    if temp is not None:
                        embed.add_field(name="Aktuell", value=f"{temp:.1f}°C", inline=True)
                    if feels_like is not None:
                        embed.add_field(name="Gefühlt", value=f"{feels_like:.1f}°C", inline=True)
                    if humidity is not None:
                        embed.add_field(name="Luftfeuchtigkeit", value=f"{humidity}%", inline=True)
                    if pressure is not None:
                        embed.add_field(name="Luftdruck", value=f"{pressure} mBar", inline=True)
                        
                    embed.add_field(name="Wind", value=f"{wind_speed_kmh:.1f} km/h", inline=False) 

                    embed.set_footer(text="Daten von OpenWeatherMap")
                    
                    await ctx.send(embed=embed)
                    
                elif response.status_code == 404:
                    await ctx.send(f"Ort '{city}' konnte nicht gefunden werden. Bitte versuchen Sie es erneut.", ephemeral=True)
                else:
                    await ctx.send(f"Fehler beim Abrufen der Wetterdaten (Code: {response.status_code}).", ephemeral=True)

            except httpx.HTTPError:
                await ctx.send("Ein Netzwerkfehler ist aufgetreten. Der Wetterdienst ist nicht erreichbar.", ephemeral=True)
            except Exception as e:
                print(f"Unerwarteter Fehler im Wetter-Befehl: {e}")
                await ctx.send("Ein unerwarteter Fehler ist aufgetreten.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))