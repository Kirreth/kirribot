import os
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from utils.database import guilds as db_guilds, joinleft as db_joinleft

# Discord Permission-Bit für Administrator-Rechte (Wert: 8)
ADMINISTRATOR_PERMISSION = 8

def create_dashboard(bot) -> FastAPI:
    app = FastAPI(title="Bot Dashboard")

    # ------------------------------------------------------------
    # Session Middleware (wichtig für OAuth!)
    # ------------------------------------------------------------
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "fallback_secret_key_123")
    )

    # ------------------------------------------------------------
    # Templates + Static
    # ------------------------------------------------------------
    templates = Jinja2Templates(directory="templates")
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # ------------------------------------------------------------
    # OAuth mit Discord
    # ------------------------------------------------------------
    oauth = OAuth()
    oauth.register(
        name="discord",
        client_id=os.getenv("DISCORD_CLIENT_ID"),
        client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
        access_token_url="https://discord.com/api/oauth2/token",
        authorize_url="https://discord.com/api/oauth2/authorize",
        api_base_url="https://discord.com/api/",
        # Wichtig: 'guilds' Scope ist nötig, um die Server des Nutzers abzurufen
        client_kwargs={"scope": "identify guilds"} 
    )

    # ------------------------------------------------------------
    # Login starten
    # ------------------------------------------------------------
    @app.get("/login")
    async def login(request: Request):
        redirect_uri = os.getenv("DISCORD_REDIRECT_URI")
        return await oauth.discord.authorize_redirect(request, redirect_uri)

    # ------------------------------------------------------------
    # Login Callback
    # ------------------------------------------------------------
    @app.get("/login/callback")
    async def login_callback(request: Request):
        token = await oauth.discord.authorize_access_token(request)
        user = token.get("userinfo") or {}
        
        # Wir leiten um und setzen das Cookie auf der Antwort
        response = RedirectResponse(url="/")
        response.set_cookie(key="discord_user", value=str(user.get("id", "unknown")))
        
        # NEU: Das vollständige Token in der Session speichern, um API-Aufrufe machen zu können
        request.session["discord_token"] = token
        
        return response

    # ------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------
    @app.get("/logout")
    async def logout(request: Request):
        # NEU: Token aus der Session löschen
        request.session.pop("discord_token", None)
        
        # Erstellt eine RedirectResponse zur Startseite
        response = RedirectResponse(url="/")
        # Löscht das Cookie, indem es mit einem leeren Wert und einer Ablauffrist in der Vergangenheit gesetzt wird
        response.delete_cookie(key="discord_user")
        return response

    # ------------------------------------------------------------
    # Nutzer-Prüfung (Gibt ID und Token zurück)
    # ------------------------------------------------------------
    def get_current_user_data(request: Request):
        user_id = request.cookies.get("discord_user")
        token = request.session.get("discord_token")
        if not user_id or not token:
            return None
        # Wir geben die ID und das Token zurück
        return {"id": user_id, "token": token}

    # ------------------------------------------------------------
    # Indexseite
    # ------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        user_data = get_current_user_data(request)
        if not user_data:
            return templates.TemplateResponse("login.html", {"request": request})

        # 1. Bot-Gilden als Set für schnellen Abgleich vorbereiten
        bot_guild_ids = {g.id for g in bot.guilds}
        
        try:
            # 2. Gilden des Nutzers über die Discord API abrufen (mit dem gespeicherten Token)
            resp = await oauth.discord.get('users/@me/guilds', token=user_data['token'])
            resp.raise_for_status() # Stellt sicher, dass bei einem Fehler (z.B. 401 Unauthorized) eine Exception geworfen wird
            user_guilds = resp.json()
        except Exception as e:
            # Bei einem Fehler (z.B. Token abgelaufen oder ungültig), leite zum Login um
            print(f"Fehler beim Abrufen der Gilden: {e}")
            # Löschen des ungültigen Tokens und Umleitung zur Neuanmeldung
            request.session.pop("discord_token", None)
            return RedirectResponse(url="/login")


        # 3. Filterung: Nur Gilden, in denen der Nutzer Admin ist UND der Bot Mitglied ist
        admin_servers = []
        for ug in user_guilds:
            try:
                # Berechtigungen prüfen: Checken ob das Administrator-Bit (8) gesetzt ist
                permissions = int(ug.get('permissions', 0))
                is_admin = (permissions & ADMINISTRATOR_PERMISSION) == ADMINISTRATOR_PERMISSION
                
                # Checken, ob der Bot auf diesem Server ist
                is_bot_present = int(ug['id']) in bot_guild_ids
                
                if is_admin and is_bot_present:
                    # Die vollständige Guild-Objekt vom Bot-Cache holen, um die korrekte Icon-URL zu generieren
                    full_guild = bot.get_guild(int(ug['id']))
                    if full_guild:
                        admin_servers.append({
                            "id": str(full_guild.id),
                            "name": full_guild.name,
                            "icon_url": full_guild.icon.with_size(64).url if full_guild.icon else None
                        })
            except Exception as e:
                # Fehler beim Parsen einer Gilde ignorieren und fortfahren
                print(f"Fehler bei Gildenverarbeitung: {e}")
                continue


        # Übergabe der gefilterten Liste an das Template
        return templates.TemplateResponse("index.html", {"request": request, "servers": admin_servers, "user": user_data['id']})

    # ------------------------------------------------------------
    # Server Dashboard (GET)
    # ------------------------------------------------------------
    @app.get("/server/{guild_id}", response_class=HTMLResponse)
    async def server_dashboard(request: Request, guild_id: str):
        # NEU: Verwendung der get_current_user_data
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")

        guild = bot.get_guild(int(guild_id))
        if not guild:
            return HTMLResponse(f"Server {guild_id} nicht gefunden", status_code=404)

        # HINWEIS: Hier sollte später noch eine dedizierte Admin-Prüfung für diesen Server erfolgen,
        # falls der Nutzer die ID direkt in die URL eingibt und nicht über die Indexseite kommt.

        # 1. Daten aus der DB holen (sie sollten Strings oder None sein)
        prefix = db_guilds.get_prefix(guild_id) or "!"
        birthday_channel = db_guilds.get_birthday_channel(guild_id)
        sanctions_channel = db_guilds.get_sanctions_channel(guild_id)
        joinleft_channel = db_joinleft.get_welcome_channel(guild_id)
        bump_channel = db_guilds.get_bump_reminder_channel(guild_id)        
        voice_channel = db_guilds.get_dynamic_voice_channel(guild_id)
        bumper_role = db_guilds.get_bumper_role(guild_id)        

        # 2. String-Konvertierung erzwingen, um Konsistenz mit Jinja2 zu gewährleisten
        bumper_role_str = str(bumper_role) if bumper_role else None
        bump_channel_str = str(bump_channel) if bump_channel else None


        return templates.TemplateResponse(
            "server_dashboard.html",
            {
                "request": request,
                "guild": guild,
                "guild_id": guild_id,
                "prefix": prefix,
                "birthday_channel": birthday_channel,
                "sanctions_channel": sanctions_channel,
                "joinleft_channel": joinleft_channel,
                
                # WICHTIG: Die konvertierten Variablen verwenden
                "bump_channel": bump_channel_str,
                "bumper_role": bumper_role_str,

                "voice_channel": voice_channel,
                "text_channels": guild.text_channels,
                "voice_channels": guild.voice_channels,
                "roles": guild.roles,
                "user": user_data['id'] # Übergabe nur der ID für die Template-Nutzung
            }
        )

    # ------------------------------------------------------------
    # POST-Update für das gesamte Dashboard-Formular
    # Behebt den 404-Fehler und verarbeitet alle Felder
    # ------------------------------------------------------------
    @app.post("/server/{guild_id}/update") 
    async def update_settings(
        guild_id: str,
        prefix: str = Form(...),
        birthday_channel: str = Form(None),
        sanctions_channel: str = Form(None),
        bump_channel: str = Form(None),
        joinleft_channel: str = Form(None),
        voice_channel: str = Form(None),
        bumper_role: str = Form(None),
    ):
        # Prefix
        db_guilds.set_prefix(guild_id, prefix)

        # Channels
        # Channel-IDs können leer sein (""), wenn im Formular "-" ausgewählt wird
        db_guilds.set_birthday_channel(guild_id, birthday_channel if birthday_channel else None)
        db_guilds.set_sanctions_channel(guild_id, sanctions_channel if sanctions_channel else None)
        db_guilds.set_bump_reminder_channel(guild_id, bump_channel if bump_channel else None)
        db_guilds.set_dynamic_voice_channel(guild_id, voice_channel if voice_channel else None)
        db_joinleft.set_welcome_channel(guild_id, joinleft_channel if joinleft_channel else None)

        # Role
        db_guilds.set_bumper_role(guild_id, bumper_role if bumper_role else None)
        
        # Zurück zum Dashboard leiten (Status 303 für "See Other" nach POST)
        return RedirectResponse(f"/server/{guild_id}", status_code=303)

    return app