import os
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from utils.database import guilds as db_guilds, joinleft as db_joinleft


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
        response = RedirectResponse(url="/")
        response.set_cookie(key="discord_user", value=str(user.get("id", "unknown")))
        return response

    # ------------------------------------------------------------
    # Nutzer-Prüfung
    # ------------------------------------------------------------
    def get_current_user(request: Request):
        user_id = request.cookies.get("discord_user")
        if not user_id:
            return None
        return user_id

    # ------------------------------------------------------------
    # Indexseite
    # ------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        user = get_current_user(request)
        if not user:
            return templates.TemplateResponse("login.html", {"request": request})
        # KORRIGIERT: Verwende g.icon.with_size(64).url, um eine korrekte CDN-URL mit fester Größe zu generieren.
        # Dies behebt das Problem, dass g.icon ein Asset-Objekt ist und die URL direkt benötigt wird.
        servers = [{"id": str(g.id), "name": g.name, "icon_url": g.icon.with_size(64).url if g.icon else None} for g in bot.guilds]
        return templates.TemplateResponse("index.html", {"request": request, "servers": servers})

    # ------------------------------------------------------------
    # Server Dashboard (GET)
    # ------------------------------------------------------------
    @app.get("/server/{guild_id}", response_class=HTMLResponse)
    async def server_dashboard(request: Request, guild_id: str):
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/login")

        guild = bot.get_guild(int(guild_id))
        if not guild:
            return HTMLResponse(f"Server {guild_id} nicht gefunden", status_code=404)

        # 1. Daten aus der DB holen (sie sollten Strings oder None sein)
        prefix = db_guilds.get_prefix(guild_id) or "!"
        birthday_channel = db_guilds.get_birthday_channel(guild_id)
        sanctions_channel = db_guilds.get_sanctions_channel(guild_id)
        joinleft_channel = db_joinleft.get_welcome_channel(guild_id)
        bump_channel = db_guilds.get_bump_reminder_channel(guild_id) 		
        voice_channel = db_guilds.get_dynamic_voice_channel(guild_id)
        bumper_role = db_guilds.get_bumper_role(guild_id) 		 

        # 2. String-Konvertierung erzwingen, um Konsistenz mit Jinja2 zu gewährleisten
        # (Selbst wenn die DB einen String zurückgibt, schadet dies nicht, aber es
        # behebt das Problem, falls der DB-Treiber einen numerischen Typ zurückgibt).

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
                "roles": guild.roles
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