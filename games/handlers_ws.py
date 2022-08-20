import json

from aiohttp import web
from aiohttp_session import get_session
from bson import ObjectId

from games.models import TicTacToeGame
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
    games_col = request.app["db"].games
    session = await get_session(request)
    user_id = session["user_id"]
    redis = request.app["redis"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    task = request.app.loop.create_task(
        redis_subscription(ws, redis, f"game_room:{game_id}")
    )

    try:
        async for msg in ws:
            game_doc = await games_col.find_one({"_id": ObjectId(game_id)})
            game = TicTacToeGame(**game_doc)

            data = json.loads(msg.data)
            if game.apply_move(user_id, data["move"]):
                await games_col.update_one(
                    {"_id": game.id},
                    {
                        "$set": {
                            "state": game.state,
                            "next_player": game.next_player,
                            "winner": game.winner,
                        }
                    },
                )
                if game.winner:
                    winner_id = game.winner["id"]
                    users_col = request.app["db"].users
                    await users_col.update_one(
                        {"_id": ObjectId(winner_id)}, {"$inc": {"games_won": 1}}
                    )

                msg = {
                    "type": "update_state",
                    "state": game.state,
                    "next": game.next_player,
                    "winner": game.winner,
                }
                await redis.publish(f"game_room:{game_id}", json.dumps(msg))
    finally:
        task.cancel()

    return ws
