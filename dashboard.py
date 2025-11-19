import os
import jwt
import datetime
import httpx
import asyncio
import logging
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from utils.database import guilds as db_guilds, joinleft as db_joinleft
from utils.database import custom_commands as db_custom

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------
BOT_ID = int(os.getenv("BOT_ID", 0))
ADMINISTRATOR_PERMISSION = 8
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60
BOT_API_URL = os.getenv("BOT_API_URL", "http://kirribot:8001")

# ------------------------------------------------------------
# JWT Hilfsfunktionen
# ------------------------------------------------------------
def create_jwt_token(user_id: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"sub": user_id, "exp": expiration}
    token_bytes = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token_bytes.decode("utf-8") if isinstance(token_bytes, bytes) else token_bytes

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# ------------------------------------------------------------
# Dashboard-App
# ------------------------------------------------------------
def create_dashboard(bot=None) -> FastAPI:
    app = FastAPI(title="Bot Dashboard")

    # Session Middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "fallback_secret_key_123"),
        https_only=True
    )

    # Templates & Static
    templates = Jinja2Templates(directory="templates")
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # OAuth mit Discord
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
    # Auth-Routen
    # ------------------------------------------------------------
    @app.get("/login")
    async def login(request: Request):
        redirect_uri = os.getenv("DISCORD_REDIRECT_URI")
        return await oauth.discord.authorize_redirect(request, redirect_uri)

    @app.get("/login/callback")
    async def login_callback(request: Request):
        try:
            token = await oauth.discord.authorize_access_token(request)
        except Exception as e:
            logger.error(f"OAuth Fehler: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="OAuth Login fehlgeschlagen.")

        resp = await oauth.discord.get('users/@me', token=token)
        user = resp.json()
        user_id = str(user.get("id"))
        if not user_id:
            raise HTTPException(status_code=400, detail="Discord-User konnte nicht ermittelt werden.")

        jwt_token = create_jwt_token(user_id)
        request.session["discord_token"] = token
        response = RedirectResponse(url="/")
        response.set_cookie(key="discord_user", value=user_id, httponly=True)
        response.set_cookie(key="jwt_token", value=jwt_token, httponly=True)
        return response

    @app.get("/logout")
    async def logout(request: Request):
        request.session.pop("discord_token", None)
        response = RedirectResponse(url="/")
        response.delete_cookie(key="discord_user")
        response.delete_cookie(key="jwt_token")
        return response

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

        # Gilden vom Bot-Service abrufen
        bot_guild_ids = set()
        max_retries = 10
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{BOT_API_URL}/api/guilds")
                    response.raise_for_status()
                    bot_guild_ids = set(response.json().get("guild_ids", []))
                    break
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Bot-API nicht erreichbar (Versuch {attempt+1}/{max_retries}). Warte {retry_delay}s. Fehler: {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Konnte Bot-Gildenliste nicht abrufen. Fehler: {e}", exc_info=True)
            except httpx.HTTPError as e:
                logger.error(f"HTTP-Fehler beim Abrufen der Bot-Gildenliste: {e}", exc_info=True)
                break

        # Discord-Gilden des Users abrufen
        try:
            resp = await oauth.discord.get('users/@me/guilds', token=user_data['token'])
            resp.raise_for_status()
            user_guilds = resp.json()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Gilden von Discord: {e}", exc_info=True)
            request.session.pop("discord_token", None)
            return RedirectResponse(url="/login")

        admin_servers = []
        for ug in user_guilds:
            try:
                permissions = int(ug.get('permissions', 0))
                is_admin = (permissions & ADMINISTRATOR_PERMISSION) == ADMINISTRATOR_PERMISSION
                is_bot_present = ug['id'] in bot_guild_ids
                if is_admin and is_bot_present:
                    icon_hash = ug.get('icon')
                    icon_url = f"https://cdn.discordapp.com/icons/{ug['id']}/{icon_hash}.png?size=64" if icon_hash else None
                    admin_servers.append({"id": ug['id'], "name": ug['name'], "icon_url": icon_url})
            except Exception as e:
                logger.warning(f"Fehler bei Gildenverarbeitung (ID: {ug.get('id', 'N/A')}): {e}", exc_info=True)
                continue

        logger.info(f"Dashboard: {len(admin_servers)} Server für Nutzer {user_data['id']} verfügbar.")
        return templates.TemplateResponse("index.html", {"request": request, "servers": admin_servers, "user": user_data['id']})

    # ------------------------------------------------------------
    # Server Dashboard
    # ------------------------------------------------------------
    @app.get("/server/{guild_id}", response_class=HTMLResponse)
    async def server_dashboard(request: Request, guild_id: str):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")

        # Gilden-Details abrufen
        max_retries = 5
        retry_delay = 3
        guild_details = {}
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{BOT_API_URL}/api/guild/{guild_id}")
                    response.raise_for_status()
                    guild_details = response.json()
                    break
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Bot-API nicht erreichbar (Versuch {attempt+1}/{max_retries}). Warte {retry_delay}s. Fehler: {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Konnte Gilden-Details nicht abrufen. Fehler: {e}", exc_info=True)
                    return HTMLResponse("Fehler beim Verbinden mit dem Bot-Service. Bitte später versuchen.", status_code=500)
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP-Fehler beim Abrufen der Gilden-Details: {e}", exc_info=True)
                return HTMLResponse("Fehler beim Bot-Service.", status_code=e.response.status_code)

        # Einstellungen aus DB
        channel_settings = {
            "birthday_channel": str(db_guilds.get_birthday_channel(guild_id) or ""),
            "sanctions_channel": str(db_guilds.get_sanctions_channel(guild_id) or ""),
            "joinleft_channel": str(db_joinleft.get_welcome_channel(guild_id) or ""),
            "bump_channel": str(db_guilds.get_bump_reminder_channel(guild_id) or ""),
            "voice_channel": str(db_guilds.get_dynamic_voice_channel(guild_id) or ""),
            "bumper_role": str(db_guilds.get_bumper_role(guild_id) or "")
        }
        prefix = db_guilds.get_prefix(guild_id) or "!"

        raw_custom_commands = db_custom.get_all_commands(guild_id) or {}
        custom_commands = {}
        if isinstance(raw_custom_commands, list):
            for cmd in raw_custom_commands:
                name = cmd.get("name")
                response = cmd.get("response")
                if name and response:
                    custom_commands[name] = response
        elif isinstance(raw_custom_commands, dict):
            custom_commands = raw_custom_commands

        return templates.TemplateResponse(
            "server_dashboard.html",
            {
                "request": request,
                "guild": guild_details,
                "guild_id": guild_id,
                "prefix": prefix,
                **channel_settings,
                "text_channels": guild_details.get("text_channels", []),
                "voice_channels": guild_details.get("voice_channels", []),
                "roles": guild_details.get("roles", []),
                "custom_commands": custom_commands,
                "user": user_data['id']
            }
        )

    # ------------------------------------------------------------
    # POST-Update für Dashboard-Formular
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
    # Custom Commands
    # ------------------------------------------------------------
    @app.post("/server/{guild_id}/commands/add")
    async def add_custom_command(request: Request, guild_id: str, command_name: str = Form(...), response: str = Form(...)):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")

        db_custom.add_command(guild_id, command_name.lower(), response)
        return RedirectResponse(f"/server/{guild_id}", status_code=303)

    @app.post("/server/{guild_id}/commands/remove")
    async def remove_custom_command(request: Request, guild_id: str, command_name: str = Form(...)):
        user_data = get_current_user_data(request)
        if not user_data:
            return RedirectResponse(url="/login")

        removed = db_custom.remove_command(guild_id, command_name.lower())
        if not removed:
            logger.warning(f"Command '{command_name}' konnte nicht gelöscht werden oder existierte nicht.")

        return RedirectResponse(f"/server/{guild_id}", status_code=303)

    return app
