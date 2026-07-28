import asyncio
from app.core.database import get_database


async def clear_all_rate_limits():
    db = await get_database()
    
    # Delete all rate limit records
    delete_result = await db.rate_limits.delete_many({})
    
    print(f"Deleted {delete_result.deleted_count} rate limit records!")


if __name__ == "__main__":
    asyncio.run(clear_all_rate_limits())
