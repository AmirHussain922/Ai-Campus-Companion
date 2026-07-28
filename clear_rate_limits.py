import asyncio
import sys
sys.path.insert(0, 'backend')
from app.database import get_database

async def main():
    db = await get_database()
    await db.rate_limits.delete_many({})
    await db.otps.delete_many({"email": {"$regex": "password_reset_test"}})
    await db.users.delete_many({"email": {"$regex": "password_reset_test"}})
    print("Cleared rate limits and test data")

asyncio.run(main())
