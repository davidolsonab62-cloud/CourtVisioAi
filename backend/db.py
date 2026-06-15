"""MongoDB connection singleton."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

_client: AsyncIOMotorClient | None = None
_db = None


def init_db():
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        _db = _client[os.environ["DB_NAME"]]
    return _db


def get_db():
    if _db is None:
        return init_db()
    return _db


async def ensure_indexes():
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.games.create_index("start_time")
    await db.games.create_index("league_id")
    await db.games.create_index("status")
    await db.predictions.create_index("game_id", unique=True)
    await db.payment_transactions.create_index("session_id", unique=True)


def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
