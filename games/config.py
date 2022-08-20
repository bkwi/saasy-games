from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent
STATIC_FILES_PATH = BASE_PATH / "static"

APP_SECRET = b"thisIsNotSecure-xxxxxxx-dontUseThisOnProdXX="

MONGO_HOST = "mongo"
MONGO_DB = "sassy_db"

REDIS_HOST = "redis"

COOKIE_NAME = "SAASY_COOKIE"
