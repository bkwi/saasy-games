from aiohttp import web
from aiohttp_session import get_session
from bson import ObjectId

from games.models import User


def login_required(func):
    """
    Check if user is signed in.
    If yes, get user from DB and update the request object.
    """

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
    """
    Create a subscription for each websocket connection.
    """
    pubsub = redis.pubsub(ignore_subscribe_messages=True)

    try:
        await pubsub.subscribe(channel_name)
        async for msg in pubsub.listen():
            await websocket.send_str(msg.get("data"))
    finally:
        await pubsub.unsubscribe(channel_name)


async def cleanup(redis, keys_to_delete=None, messages_to_publish=None):
    """
    Cleanup pending game data when player joins (or game is cancelled).
    Puglish messages to update home screen.
    """
    keys_to_delete = keys_to_delete or {}
    messages_to_publish = messages_to_publish or {}

    for set_name, key in keys_to_delete.items():
        await redis.hdel(set_name, key)

    for channel, msg in messages_to_publish.items():
        await redis.publish(channel, msg)
