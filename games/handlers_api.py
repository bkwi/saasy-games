import hashlib
import json
import os
import secrets

from aiohttp import web
from aiohttp_session import get_session, new_session
from bson import ObjectId

from games.models import GAME_TYPES, User
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

    if data["opponent"]["type"] == "cpu":
        game_class = GAME_TYPES[data["game"]["codename"]]
        game = game_class(_id=ObjectId(game_id))
        game.start(
            players=[
                {
                    "id": str(user.id),
                    "username": user.username,
                },
                {
                    "id": "cpu",
                    "username": "Computer",
                },
            ]
        )
        await request.app["db"].games.insert_one(game.db_dict())
        await request.app["db"].users.update_one(
            {"_id": user.id}, {"$inc": {"games_played": 1}}
        )
        game_data = {
            "game_id": game_id,
            "name": game.display_name,
            "players": [p["username"] for p in game.players],
        }
        await request.app["redis"].hset("games_ongoing", game_id, json.dumps(game_data))
        await request.app["redis"].publish(
            "main_room",
            json.dumps({"type": "games_added", "ongoing_games": [game_data]}),
        )
        return web.json_response({"redirect_url": f"/game-room/{game_id}"})

    pending_game = {
        "game_id": game_id,
        "game": data["game"],
        "host_id": str(user.id),
        "host_username": user.username,
        "opponent": data["opponent"],
    }

    redis = request.app["redis"]
    await redis.hset("games_pending", game_id, json.dumps(pending_game))
    await redis.publish(
        "main_room",
        json.dumps({"type": "games_added", "pending_games": [pending_game]}),
    )
    return web.json_response({"redirect_url": f"/waiting-room/{game_id}"})


@routes.post("/api/join-game")
@login_required
async def join_game(request: web.Request) -> web.Response:
    data = await request.json()
    game_id = data["game_id"]
    user = request["user"]
    redis = request.app["redis"]
    pending_game = json.loads(await redis.hget("games_pending", game_id))

    if str(user.id) == pending_game["host_id"]:
        return web.json_response({"msg": "you can't join your own game"}, status=400)

    await redis.hdel("games_pending", game_id)

    users_col = request.app["db"].users
    host_user_doc = await users_col.find_one({"_id": ObjectId(pending_game["host_id"])})
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

    game_class = GAME_TYPES[pending_game["game"]["codename"]]
    game = game_class(_id=ObjectId(game_id))
    game.start(players=players)
    await request.app["db"].games.insert_one(game.db_dict())
    await request.app["db"].users.update_many(
        {"_id": {"$in": [host.id, user.id]}}, {"$inc": {"games_played": 1}}
    )
    game_data = {
        "game_id": game_id,
        "name": game.display_name,
        "players": [p["username"] for p in game.players],
    }
    await request.app["redis"].hset("games_ongoing", game_id, json.dumps(game_data))
    await redis.publish(f"waiting_room:{game_id}", "game_ready")
    await redis.publish(
        "main_room",
        json.dumps({"type": "games_added", "ongoing_games": [game_data]}),
    )

    return web.json_response({"msg": "ok"})


@routes.get("/api/pending-games")
@login_required
async def pending_games(request: web.Request) -> web.Response:
    redis = request.app["redis"]
    games = [
        json.loads(game) for _, game in (await redis.hgetall("games_pending")).items()
    ]
    return web.json_response({"games": games})


@routes.get("/api/ongoing-games")
async def ongoing_games(request: web.Request) -> web.Response:
    redis = request.app["redis"]
    games = [
        json.loads(game) for _, game in (await redis.hgetall("games_ongoing")).items()
    ]
    return web.json_response({"games": games})


@routes.get(r"/api/game-room/{game_id:\w+}")
async def game_room(request: web.Request) -> web.Response:
    game_id = request.match_info["game_id"]
    games_col = request.app["db"].games
    game_doc = await games_col.find_one({"_id": ObjectId(game_id)})
    if not game_doc:
        return web.json_response({"msg": "game not found"}, status=404)

    game_class = GAME_TYPES[game_doc["code_name"]]
    game = game_class(**game_doc)
    return web.json_response(
        {"state": game.state, "next": game.next_player, "players": game.players}
    )


@routes.post("/api/game/move")
@login_required
async def make_move(request: web.Request) -> web.Response:
    data = await request.json()
    game_id = data["game_id"]
    user = request["user"]
    game_doc = await request.app["db"].games.find_one({"_id": ObjectId(game_id)})
    game = GAME_TYPES[game_doc["code_name"]](**game_doc)

    if str(user.id) not in [player["id"] for player in game.players]:
        return web.json_response(
            {"msg": "you're not taking part in this game"}, status=403
        )

    if game.apply_move(str(user.id), data["move"]):
        await request.app["db"].games.update_one(
            {"_id": game.id},
            {
                "$set": {
                    "state": game.state,
                    "next_player": game.next_player,
                    "winner": game.winner,
                }
            },
        )
        if game.winner and game.winner["id"] != "cpu":
            await request.app["db"].users.update_one(
                {"_id": ObjectId(game.winner["id"])}, {"$inc": {"games_won": 1}}
            )

        if game.finished:
            await request.app["redis"].hdel("games_ongoing", game_id)
            await request.app["redis"].publish(
                "main_room",
                json.dumps({"type": "games_removed", "ongoing_games": [game_id]}),
            )

        msg = {
            "type": "update_state",
            "state": game.state,
            "next": game.next_player,
            "winner": game.winner,
            "finished": game.finished,
        }
        await request.app["redis"].publish(f"game_room:{game_id}", json.dumps(msg))

    return web.json_response({})


@routes.get("/api/stats")
async def stats(request: web.Request) -> web.Response:
    games_col = request.app["db"].games
    stats = {"total_games_played": await games_col.count_documents({})}

    session = await get_session(request)
    if user_id := session.get("user_id"):
        users_col = request.app["db"].users
        user_doc = await users_col.find_one({"_id": ObjectId(user_id)})
        user = User(**user_doc)
        stats.update(
            {
                "user_games_played": user.games_played,
                "user_games_won": user.games_won,
            }
        )

    return web.json_response(stats)
