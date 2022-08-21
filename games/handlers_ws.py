from aiohttp import web
from aiohttp_session import get_session

from games.utils import login_required, redis_subscription

routes = web.RouteTableDef()


@routes.get("/ws")
async def open_ws(request):
    ws = web.WebSocketResponse()
    session = await get_session(request)
    await ws.prepare(request)
    request.app["websockets"][session["browser_id"]].add(ws)

    try:
        async for msg in ws:
            await ws.send_str(msg.data)
    finally:
        pass

    return ws


@routes.get(r"/ws/waiting-room/{game_id:\w+}")
@login_required
async def waiting_room(request: web.Request) -> web.WebSocketResponse:
    game_id = request.match_info["game_id"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    task = request.app.loop.create_task(
        redis_subscription(ws, request.app["redis"], f"waiting_room:{game_id}")
    )
    try:
        async for msg in ws:
            pass
    finally:
        task.cancel()
        await request.app["redis"].hdel("games_pending", game_id)

    return ws


@routes.get(r"/ws/game-room/{game_id:\w+}")
async def game_room(request: web.Request) -> web.WebSocketResponse:
    game_id = request.match_info["game_id"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    task = request.app.loop.create_task(
        redis_subscription(ws, request.app["redis"], f"game_room:{game_id}")
    )

    try:
        async for msg in ws:
            pass
    finally:
        task.cancel()

    return ws
