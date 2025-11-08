import os
import jwt
import datetime
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from utils.database import guilds as db_guilds, joinleft as db_joinleft
from utils.database import custom_commands as db_custom

ADMINISTRATOR_PERMISSION = 8
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60  # 1 Stunde

# ------------------------------------------------------------
# JWT Hilfsfunktionen
# ------------------------------------------------------------
def create_jwt_token(user_id: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"sub": user_id, "exp": expiration}
    token_bytes = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT 2.x gibt bytes zurück, wir brauchen str für Cookies
    if isinstance(token_bytes, bytes):
        return token_bytes.decode("utf-8")
    return token_bytes

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ------------------------------------------------------------
# Dashboard-Funktion
# ------------------------------------------------------------
def create_dashboard(bot) -> FastAPI:
    app = FastAPI(title="Bot Dashboard")

    # ------------------------------------------------------------
    # Session Middleware für OAuth
    # ------------------------------------------------------------
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "fallback_secret_key_123"),
        https_only=True  # Bei HTTPS aktivieren, bei HTTP testen ggf. False
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
        client_kwargs={"scope": "identify email guilds"}
    )

    # ------------------------------------------------------------
    # Login starten
    # ------------------------------------------------------------
    @app.get("/login")
    async def login(request: Request):
        redirect_uri = os.getenv("DISCORD_REDIRECT_URI")
        # Authlib erstellt intern den 'state' und speichert ihn in der Session
        return await oauth.discord.authorize_redirect(request, redirect_uri)

    # ------------------------------------------------------------
    # Login Callback mit JWT-Erzeugung
    # ------------------------------------------------------------
    @app.get("/login/callback")
    async def login_callback(request: Request):
        try:
            token = await oauth.discord.authorize_access_token(request)
        except Exception as e:
            # State-Mismatch oder andere Auth-Fehler
            print(f"OAuth Fehler: {e}")
            raise HTTPException(status_code=400, detail="OAuth Login fehlgeschlagen.")

        # Discord User abrufen
        resp = await oauth.discord.get('users/@me', token=token)
        user = resp.json()
        user_id = str(user.get("id"))
        if not user_id:
            raise HTTPException(status_code=400, detail="Discord-User konnte nicht ermittelt werden.")

        # JWT erstellen
        jwt_token = create_jwt_token(user_id)

        # Session + Cookies setzen
        request.session["discord_token"] = token  # Authlib braucht die Session
        response = RedirectResponse(url="/")
        response.set_cookie(key="discord_user", value=user_id, httponly=True)
        response.set_cookie(key="jwt_token", value=jwt_token, httponly=True)
        return response

    # ------------------------------------------------------------
    # Logout – Session + JWT löschen
    # ------------------------------------------------------------
    @app.get("/logout")
    async def logout(request: Request):
        request.session.pop("discord_token", None)
        response = RedirectResponse(url="/")
        response.delete_cookie(key="discord_user")
        response.delete_cookie(key="jwt_token")
        return response

    # ------------------------------------------------------------
    # Nutzer-Prüfung (Discord + JWT)
    # ------------------------------------------------------------
    def get_current_user_data(request: Request):
        user_id = request.cookies.get("discord_user")
        jwt_token = request.cookies.get("jwt_token")
        token = request.session.get("discord_token")

        if not user_id or not token or not jwt_token:
            return None

        verified_id = verify_jwt_token(jwt_token)
        if not verified_id or verified_id != user_id:
            return None

        return {"id": user_id, "token": token}

    # ------------------------------------------------------------
    # Indexseite
    # ------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        user_data = get_current_user_data(request)
        if not user_data:
            return templates.TemplateResponse("login.html", {"request": request})

        bot_guild_ids = {g.id for g in bot.guilds}
        try:
            resp = await oauth.discord.get('users/@me/guilds', token=user_data['token'])
            user_guilds = resp.json()
        except Exception as e:
            print(f"Fehler beim Abrufen der Gilden: {e}")
            request.session.pop("discord_token", None)
            return RedirectResponse(url="/login")

        admin_servers = []
        for ug in user_guilds:
            try:
                permissions = int(ug.get('permissions', 0))
                is_admin = (permissions & ADMINISTRATOR_PERMISSION) == ADMINISTRATOR_PERMISSION
                is_bot_present = int(ug['id']) in bot_guild_ids
                if is_admin and is_bot_present:
                    full_guild = bot.get_guild(int(ug['id']))
                    if full_guild:
                        admin_servers.append({
                            "id": str(full_guild.id),
                            "name": full_guild.name,
                            "icon_url": full_guild.icon.with_size(64).url if full_guild.icon else None
                        })
            except Exception as e:
                print(f"Fehler bei Gildenverarbeitung: {e}")
                continue

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "servers": admin_servers, "user": user_data['id']}
        )

    # ------------------------------------------------------------
    # Server Dashboard (GET)
    # ------------------------------------------------------------
    @app.get("/server/{guild_id}", response_class=HTMLResponse)
    async def server_dashboard(request: Request, guild_id: str):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")

        guild = bot.get_guild(int(guild_id))
        if not guild:
            return HTMLResponse(f"Server {guild_id} nicht gefunden", status_code=404)

        prefix = db_guilds.get_prefix(guild_id) or "!"
        birthday_channel = db_guilds.get_birthday_channel(guild_id)
        sanctions_channel = db_guilds.get_sanctions_channel(guild_id)
        joinleft_channel = db_joinleft.get_welcome_channel(guild_id)
        bump_channel = db_guilds.get_bump_reminder_channel(guild_id)
        voice_channel = db_guilds.get_dynamic_voice_channel(guild_id)
        bumper_role = db_guilds.get_bumper_role(guild_id)
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
                "bump_channel": bump_channel_str,
                "bumper_role": bumper_role_str,
                "voice_channel": voice_channel,
                "text_channels": guild.text_channels,
                "voice_channels": guild.voice_channels,
                "roles": guild.roles,
                "user": user_data['id']
            }
        )

    # ------------------------------------------------------------
    # POST-Update für das Dashboard-Formular
    # ------------------------------------------------------------
    @app.post("/server/{guild_id}/update")
    async def update_settings(
        request: Request,
        guild_id: str,
        prefix: str = Form(...),
        birthday_channel: str = Form(None),
        sanctions_channel: str = Form(None),
        bump_channel: str = Form(None),
        joinleft_channel: str = Form(None),
        voice_channel: str = Form(None),
        bumper_role: str = Form(None),
    ):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")

        db_guilds.set_prefix(guild_id, prefix)
        db_guilds.set_birthday_channel(guild_id, birthday_channel or None)
        db_guilds.set_sanctions_channel(guild_id, sanctions_channel or None)
        db_guilds.set_bump_reminder_channel(guild_id, bump_channel or None)
        db_guilds.set_dynamic_voice_channel(guild_id, voice_channel or None)
        db_joinleft.set_welcome_channel(guild_id, joinleft_channel or None)
        db_guilds.set_bumper_role(guild_id, bumper_role or None)

        return RedirectResponse(f"/server/{guild_id}", status_code=303)
    # ------------------------------------------------------------
    # Custom Command Verwaltung (Import der Routen)
    # ------------------------------------------------------------
    

    @app.post("/server/{guild_id}/commands/add")
    async def add_custom_command(request: Request, guild_id: str, command_name: str = Form(...), response: str = Form(...)):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")
        
        db_custom.add_command(guild_id, command_name.lower(), response)
        return RedirectResponse(url=f"/server/{guild_id}", status_code=303)

    # Command löschen
    @app.post("/server/{guild_id}/commands/remove")
    async def remove_custom_command(request: Request, guild_id: str, command_name: str = Form(...)):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")
        
        db_custom.remove_command(guild_id, command_name.lower())
        return RedirectResponse(url=f"/server/{guild_id}", status_code=303)

    return app
