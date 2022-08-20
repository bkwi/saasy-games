import hashlib
import json
import os
import random
import secrets

from aiohttp import web
from aiohttp_session import get_session, new_session
from bson import ObjectId

from games.models import TicTacToeGame, User
from games.utils import login_required

routes = web.RouteTableDef()


@routes.post("/api/login")
async def login(request: web.Request) -> web.Response:
    data = await request.json()

    user_doc = await request.app["db"].users.find_one({"username": data["username"]})
    if not user_doc:
        return web.json_response({"msg": "user not found"}, status=400)

    user = User(**user_doc)
    calculated_hash = hashlib.pbkdf2_hmac(
        "sha256", data["password"].encode(), user.pwd_salt, iterations=100_000
    )

    if secrets.compare_digest(user.pwd_hash, calculated_hash):
        old_session = await get_session(request)
        browser_id = old_session["browser_id"]
        old_session.invalidate()

        session = await new_session(request)
        session["authorized"] = True
        session["browser_id"] = browser_id
        session["user_id"] = str(user.id)
        return web.json_response({"msg": "ok"})

    return web.json_response({"msg": "auth failed"}, 401)


@routes.post("/api/register")
async def register(request: web.Request) -> web.Response:
    data = await request.json()

    users_col = request.app["db"].users

    if await users_col.count_documents({"username": data["username"]}):
        return web.json_response({"msg": "user already exists"}, status=400)

    pwd_salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", data["password"].encode(), pwd_salt, iterations=100_000
    )
    new_user = User(username=data["username"], pwd_salt=pwd_salt, pwd_hash=pwd_hash)
    users_col.insert_one(new_user.db_dict())

    return web.json_response({"msg": "ok"})


@routes.get("/api/user")
@login_required
async def get_user(request: web.Request) -> web.Response:
    user_dict = request["user"].data_dict()
    return web.json_response({"user": user_dict})


@routes.post("/api/new-game")
@login_required
async def create_new_game(request: web.Request) -> web.Response:
    data = await request.json()
    user = request["user"]
    game_id = str(ObjectId())
    game = {
        "game_id": game_id,
        "host_id": str(user.id),
        "host_username": user.username,
        "game_type": data["game_type"],
        "opponent_type": data["opponent_type"],
    }
    redis = request.app["redis"]
    await redis.hset("games_pending", game_id, json.dumps(game))
    return web.json_response({"waiting_room_id": game_id})


@routes.post("/api/join-game")
@login_required
async def join_game(request: web.Request) -> web.Response:
    data = await request.json()
    game_id = data["game_id"]
    user = request["user"]
    redis = request.app["redis"]
    game = json.loads(await redis.hget("games_pending", game_id))

    if user.id == game["host_id"]:
        return web.json_response({"msg": "you can't join your own game"}, status=400)

    await redis.hdel("games_pending", game_id)

    users_col = request.app["db"].users
    host_user_doc = await users_col.find_one({"_id": ObjectId(game["host_id"])})
    host = User(**host_user_doc)

    players = [
        {
            "id": str(host.id),
            "username": host.username,
        },
        {
            "id": str(user.id),
            "username": user.username,
        },
    ]
    chars = ["X", "O"]
    random.shuffle(players)
    players[0]["char"] = chars.pop()
    players[1]["char"] = chars.pop()

    game_obj = TicTacToeGame(
        _id=ObjectId(game_id), players=players, next_player=players[0]
    )
    games_col = request.app["db"].games
    await games_col.insert_one(game_obj.db_dict())
    await redis.publish(f"waiting_room:{game_id}", "game_ready")

    return web.json_response({"msg": "ok"})


@routes.get("/api/pending-games")
@login_required
async def pending_games(request: web.Request) -> web.Response:
    redis = request.app["redis"]
    games = [
        json.loads(game) for _, game in (await redis.hgetall("games_pending")).items()
    ]
    return web.json_response({"games": games})


@routes.get(r"/api/game-room/{game_id:\w+}")
async def game_room(request: web.Request) -> web.Response:
    game_id = request.match_info["game_id"]
    games_col = request.app["db"].games
    game_doc = await games_col.find_one({"_id": ObjectId(game_id)})
    if not game_doc:
        return web.json_response({"msg": "game not found"}, status=404)

    game = TicTacToeGame(**game_doc)
    return web.json_response(
        {"state": game.state, "next": game.next_player, "players": game.players}
    )
