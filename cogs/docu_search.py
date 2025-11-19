import discord
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote

class DocsSearch(commands.Cog):
    """
    Ein Cog zur Suche in technischer Dokumentation über Hybrid Commands.
    Befehl: /docu <sprache> <thema>
    """
    
    def __init__(self, bot):
        self.bot = bot
        
        # 📚 Konfiguration: Zuordnung der Sprachen zu ihren offiziellen Such-URLs und Farben
        self.doc_links = {
            # Bisherige Sprachen
            "py": {
                "name": "Python",
                "color": 0x3776AB,
                "base_url": "https://docs.python.org/3/search.html?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg"
            },
            "js": {
                "name": "JavaScript (MDN)",
                "color": 0xF7DF1E,
                "base_url": "https://developer.mozilla.org/en-US/search?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png"
            },
            "html": {
                "name": "HTML (MDN)",
                "color": 0xE34F26,
                "base_url": "https://developer.mozilla.org/en-US/search?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/6/61/HTML5_logo_and_wordmark.svg"
            },
            # Neue Sprachen
            "swift": {
                "name": "Swift",
                "color": 0xFA7343, # Swift Orange
                "base_url": "https://developer.apple.com/search/?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/e/ea/Swift_logo.svg"
            },
            "c": {
                "name": "C (cplusplus.com)",
                "color": 0x555555, # Dunkelgrau
                "base_url": "https://www.cplusplus.com/search.do?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/1/18/C_Programming_Language.svg"
            },
            "cpp": {
                "name": "C++",
                "color": 0x00599C, # C++ Blau
                "base_url": "https://www.cplusplus.com/search.do?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/1/18/ISO_C%2B%2B_Logo.svg"
            },
            "c#": {
                "name": "C#",
                "color": 0x9832A8, # C# Violett
                "base_url": "https://learn.microsoft.com/en-us/search/?terms=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/b/bd/Logo_C_sharp.svg"
            },
            "java": {
                "name": "Java",
                "color": 0xE76F00, # Java Orange
                "base_url": "https://docs.oracle.com/en/java/javase/search.html?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/de/e/e2/Java-Logo.svg"
            },
            "kotlin": {
                "name": "Kotlin",
                "color": 0x7F52FF, # Kotlin Violett
                "base_url": "https://kotlinlang.org/docs/home.html?search=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/7/74/Kotlin_logo.svg"
            },
            "dart": {
                "name": "Dart",
                "color": 0x0175C2, # Dart Blau
                "base_url": "https://dart.dev/search?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Dart-logo.png"
            },
            "flutter": {
                "name": "Flutter",
                "color": 0x02569B, # Flutter Blau
                "base_url": "https://docs.flutter.dev/search?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/1/17/Google-flutter-logo.svg"
            },
            "ts": {
                "name": "TypeScript",
                "color": 0x3178C6, # TypeScript Blau
                "base_url": "https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html#",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Typescript_logo_2020.svg"
            },
            "rust": {
                "name": "Rust",
                "color": 0x000000, # Schwarz
                "base_url": "https://doc.rust-lang.org/book/?search=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/d/d5/Rust_programming_language_black_logo.svg"
            },
            "go": {
                "name": "Go",
                "color": 0x00ADD8, # Go Blau
                "base_url": "https://pkg.go.dev/search?q=",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/0/05/Go_Logo_Blue.svg"
            },
            "lua": {
                "name": "Lua",
                "color": 0x000080, # Dunkelblau
                "base_url": "https://www.lua.org/manual/5.4/index.html#",
                "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Lua-language.svg/640px-Lua-language.svg.png"
            }
        }

    async def _prepare_doc_search(self, lang_key: str, query: str) -> tuple:
        """
        Interne Funktion zur Aufbereitung der Suchdaten und URL-Kodierung.
        Gibt bei Fehler: (None, Fehlermeldung)
        Gibt bei Erfolg: (name, description, url, color, icon_url)
        """
        
        doc_info = self.doc_links.get(lang_key.lower())
        
        if not doc_info:
            supported = ", ".join(self.doc_links.keys())
            # Im Fehlerfall geben wir explizit nur 2 Werte zurück
            return None, f"Unbekannte Sprache. Unterstützte Sprachen: `{supported}`."

        # Kodiert den Suchbegriff für die URL
        encoded_query = quote(query)
        search_url = doc_info["base_url"] + encoded_query
        
        # Die Beschreibung für das Embed
        description = (
            f"Führe eine Suche in der offiziellen **{doc_info['name']}** Dokumentation durch."
            f"\n\n**Suchbegriff:** `{query}`"
            "\n\n**➡️ Klicke auf den Titel, um das beste Ergebnis direkt zu sehen.**"
        )
        
        # Im Erfolgsfall geben wir 5 Werte zurück
        return (
            doc_info["name"], 
            description, 
            search_url, 
            doc_info["color"], 
            doc_info["icon_url"]
        )

    @commands.hybrid_command(
        name="docu", 
        description="Durchsucht die offizielle Dokumentation für eine Programmiersprache."
    )
    @app_commands.describe(
        sprache="Die Programmiersprache (z.B. py, js, swift)",
        thema="Der Suchbegriff (z.B. list.append, map, class inheritance)"
    )
    async def docu(self, ctx: commands.Context, sprache: str, thema: str):
        """
        Der Hauptbefehl. Sucht in der Dokumentation und sendet das Ergebnis als Embed.
        """
        # Defer stellt sicher, dass der Bot schnell reagiert
        await ctx.defer() 

        # Suchdaten vorbereiten. Das Ergebnis ist entweder ein 2er- oder 5er-Tupel.
        result = await self._prepare_doc_search(sprache, thema)

        # ------------------------------------------------------------------
        # Korrigierte Fehlerbehandlung: Prüfen, ob ein Fehler vorliegt (Länge des Tupels ist 2)
        # ------------------------------------------------------------------
        if len(result) == 2:
            # Fehlerfall: Entpacke die beiden Werte (None und Fehlermeldung)
            lang_name, description = result 
            embed = discord.Embed(
                title="❌ Docs-Search Fehler",
                description=description,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True) 
        
        # Erfolgsfall: Entpacke die fünf Werte
        lang_name, description, search_url, color, icon_url = result
        
        # Ergebnis-Embed erstellen
        embed = discord.Embed(
            title=f"🔎 {lang_name} Docs: {thema}",
            url=search_url,
            description=description,
            color=color
        )
        
        # Author/Footer-Informationen
        embed.set_author(name=lang_name, icon_url=icon_url)
        embed.set_footer(text=f"Anfrage von {ctx.author.display_name}")

        await ctx.send(embed=embed)


# 🛠️ Setup-Funktion (erforderlich, um den Cog zu laden)
async def setup(bot):
    await bot.add_cog(DocsSearch(bot))