import aiofiles
from aiohttp import web
from aiohttp_session import get_session
from bson import ObjectId

from games.utils import login_required

routes = web.RouteTableDef()


async def read_html(filename: str) -> str:
    async with aiofiles.open(f"/app/templates/{filename}") as html:
        return await html.read()


@routes.get("/favicon.ico")
async def favicon(request: web.Request) -> web.Response:
    return web.Response()


@routes.get("/")
async def index(request: web.Request) -> web.Response:
    return web.Response(text=await read_html("index.html"), content_type="text/html")


@routes.get("/login")
async def login(request: web.Request) -> web.Response:
    return web.Response(text=await read_html("login.html"), content_type="text/html")


@routes.get("/logout")
async def logout(request: web.Request) -> web.Response:
    session = await get_session(request)
    session.invalidate()
    raise web.HTTPFound(location="/")


@routes.get("/register")
async def register(request: web.Request) -> web.Response:
    return web.Response(text=await read_html("register.html"), content_type="text/html")


@routes.get(r"/waiting-room/{room_id:\w+}")
async def waiting_room(request: web.Request) -> web.Response:
    return web.Response(
        text=await read_html("waiting_room.html"), content_type="text/html"
    )


@routes.get(r"/game-room/{game_id:\w+}")
@login_required
async def game_room(request: web.Request) -> web.Response:
    game_id = request.match_info["game_id"]
    projection = await request.app["db"].games.find_one(
        {"_id": ObjectId(game_id)}, projection={"players": 1}
    )
    user = request["user"]
    player_ids = [p["id"] for p in projection["players"]]
    if str(user.id) not in player_ids:
        raise web.HTTPNotFound()

    return web.Response(
        text=await read_html("game_room.html"), content_type="text/html"
    )


@routes.get(r"/spectate/{game_id:\w+}")
async def spectate(request: web.Request) -> web.Response:
    return web.Response(
        text=await read_html("game_room.html"), content_type="text/html"
    )
