import aiofiles
from aiohttp import web
from aiohttp_session import get_session

routes = web.RouteTableDef()


async def read_html(filename: str) -> str:
    async with aiofiles.open(f"/app/templates/{filename}") as html:
        return await html.read()


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


@routes.get("/fanout")
async def foo(request):
    redis = request.app["redis"]
    db = request.app["db"]
    # await redis.publish(
    #     "ttt",
    #     "game_ready"
    #     # "waiting_room:cabd0f8336b14b868992df226aa5509a", "hello everyone"
    # )

    cur = db.games.find({})
    async for item in cur:
        print(item)

    # await db.games.drop()
    return web.Response(text="HEY")


@routes.get(r"/waiting-room/{room_id:\w+}")
async def waiting_room(request: web.Request) -> web.Response:
    return web.Response(
        text=await read_html("waiting_room.html"), content_type="text/html"
    )


@routes.get(r"/game-room/{game_id:\w+}")
async def game_room(request: web.Request) -> web.Response:
    return web.Response(
        text=await read_html("game_room.html"), content_type="text/html"
    )
