import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "finance_tracker")

_using_mock = False

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    _HAS_MOTOR = True
except ImportError:
    _HAS_MOTOR = False
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None
    ConnectionFailure = Exception
    ServerSelectionTimeoutError = Exception

_client: Optional["AsyncIOMotorClient"] = None
_db: Optional["AsyncIOMotorDatabase"] = None


async def connect_db():
    global _client, _db, _using_mock
    if not _HAS_MOTOR:
        logger.warning("motor not installed — using mongomock-motor fallback")
        return await _connect_mock()
    try:
        _client = AsyncIOMotorClient(
            MONGODB_URI, maxPoolSize=10, minPoolSize=1, serverSelectionTimeoutMS=5000,
        )
        _db = _client[DATABASE_NAME]
        await _client.admin.command("ping")
        logger.info("Connected to MongoDB at %s / %s", MONGODB_URI, DATABASE_NAME)
        await _ensure_indexes()
        return _db
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable (%s) — falling back to mongomock-motor", e)
        return await _connect_mock()


async def _connect_mock():
    global _client, _db, _using_mock
    try:
        from mongomock_motor import AsyncMongoMockClient
        _client = AsyncMongoMockClient()
        _db = _client[DATABASE_NAME]
        _using_mock = True
        logger.info("Connected to in-memory mock MongoDB")
        await _ensure_indexes()
        return _db
    except ImportError:
        logger.error("mongomock-motor not installed — cannot operate without MongoDB")
        raise RuntimeError("No database backend available. Install mongomock-motor or start MongoDB.")


async def close_db() -> None:
    global _client, _db
    if _client and not _using_mock:
        _client.close()
    _client = None
    _db = None
    logger.info("Database connection closed")


async def get_db():
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db


async def health_check() -> dict:
    try:
        if _client:
            await _client.admin.command("ping")
            mode = "mock" if _using_mock else "connected"
            return {"status": mode, "database": DATABASE_NAME}
        return {"status": "disconnected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def _ensure_indexes() -> None:
    if _db is None:
        return
    transactions = _db["transactions"]
    await transactions.create_index("date")
    await transactions.create_index("category")
    await transactions.create_index("user_id")
    await transactions.create_index("status")
    await transactions.create_index([("user_id", 1), ("date", -1)])
    budgets = _db["budgets"]
    await budgets.create_index("user_id")
    await budgets.create_index([("user_id", 1), ("month", 1)], unique=True)
    alerts = _db["alerts"]
    await alerts.create_index("user_id")
    await alerts.create_index([("user_id", 1), ("created_at", -1)])
    logger.info("Database indexes ensured")


class MongoDB:
    async def connect(self):
        return await connect_db()

    async def close(self):
        await close_db()

    async def get_db(self):
        return await get_db()

    async def health(self):
        return await health_check()
