import json

from aiohttp import web

from games.utils import cleanup, login_required, redis_subscription

routes = web.RouteTableDef()


@routes.get("/ws/main")
async def open_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    task = request.app.loop.create_task(
        redis_subscription(ws, request.app["redis"], "main_room")
    )

    try:
        async for msg in ws:
            await ws.send_str(msg.data)
    finally:
        task.cancel()

    return ws


@routes.get(r"/ws/waiting-room/{game_id:\w+}")
@login_required
async def waiting_room(request: web.Request) -> web.WebSocketResponse:
    game_id = request.match_info["game_id"]
    ws = web.WebSocketResponse(heartbeat=1.0)
    await ws.prepare(request)
    redis = request.app["redis"]

    task = request.app.loop.create_task(
        redis_subscription(ws, redis, f"waiting_room:{game_id}")
    )
    try:
        await ws.receive()
    finally:
        request.app.loop.create_task(
            cleanup(
                redis,
                {"games_pending": game_id},
                {
                    "main_room": json.dumps(
                        {"type": "games_removed", "pending_games": [game_id]}
                    ),
                },
            )
        )
        task.cancel()

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
