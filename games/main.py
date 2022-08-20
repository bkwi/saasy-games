import base64
import uuid
from collections import defaultdict
from typing import Awaitable

import aiohttp_session
import aioredis
import motor.motor_asyncio
from aiohttp import web
from aiohttp_session import get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from games import config
from games.handlers_api import routes as api_routes
from games.handlers_web import routes as web_routes
from games.handlers_ws import routes as ws_routes


@web.middleware
async def session_middleware(request: web.Request, handler: Awaitable) -> web.Response:
    session = await get_session(request)
    if not session:
        session["browser_id"] = uuid.uuid4().hex
    return await handler(request)


async def setup_app_redis(app: web.Application):
    app["redis"] = aioredis.from_url(
        f"redis://{config.REDIS_HOST}", decode_responses=True, db=0
    )
    yield


async def setup_db(app: web.Application):
    client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_HOST, 27017)
    app["db"] = client[config.MONGO_DB]
    yield


async def create_app() -> web.Application:

    app = web.Application()

    aiohttp_session.setup(
        app,
        EncryptedCookieStorage(
            base64.urlsafe_b64decode(config.APP_SECRET),
            cookie_name=config.COOKIE_NAME,
        ),
    )

    app.middlewares.extend([session_middleware])
    app.cleanup_ctx.extend([setup_app_redis, setup_db])

    app["websockets"] = defaultdict(set)

    app.add_routes(web_routes)
    app.add_routes(api_routes)
    app.add_routes(ws_routes)
    app.add_routes([web.static("/static", config.STATIC_FILES_PATH)])

    return app


if __name__ == "__main__":
    web.run_app(create_app(), port=8000, host="0.0.0.0")
