from aiohttp import web
from aiohttp_session import get_session
from bson import ObjectId

from games.models import User


def login_required(func):
    async def wrapper(request: web.Request):
        session = await get_session(request)
        if session.get("authorized"):
            user_id = session["user_id"]
            user_doc = await request.app["db"].users.find_one(
                {"_id": ObjectId(user_id)}
            )
            request["user"] = User(**user_doc)
            return await func(request)

        return web.Response(status=401)

    return wrapper


async def redis_subscription(websocket, redis, channel_name: str):
    pubsub = redis.pubsub(ignore_subscribe_messages=True)

    try:
        await pubsub.subscribe(channel_name)
        async for msg in pubsub.listen():
            print("IN PUB LISTEN", msg)
            await websocket.send_str(msg.get("data"))
    finally:
        await pubsub.unsubscribe(channel_name)
