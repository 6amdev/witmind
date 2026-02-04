"""
MongoDB connection using Motor (async driver)
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from .config import settings


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None


db = Database()


async def connect_db():
    """Connect to MongoDB"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB]
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB}")


async def disconnect_db():
    """Disconnect from MongoDB"""
    if db.client:
        db.client.close()
        print("❌ Disconnected from MongoDB")


def get_db():
    """Get database instance"""
    return db.db


# Collections
def get_collection(name: str):
    """Get a collection by name"""
    return db.db[name]


# Shorthand for common collections
def projects_collection():
    return get_collection("projects")


def tasks_collection():
    return get_collection("tasks")


def activities_collection():
    return get_collection("activities")


def agents_collection():
    return get_collection("agents")


def users_collection():
    return get_collection("users")


def approvals_collection():
    return get_collection("approvals")


def agent_commands_collection():
    return get_collection("agent_commands")
