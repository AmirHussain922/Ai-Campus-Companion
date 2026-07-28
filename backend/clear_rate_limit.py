import asyncio
from app.core.database import get_database
from app.utils.rate_limiter import RateLimitAction


async def clear_rate_limits():
    email = "hamir6464@gmail.com"
    action = RateLimitAction.PASSWORD_RESET
    key = f"{action.value}:{email.lower()}"
    block_key = f"block:{key}"
    
    db = await get_database()
    
    # Delete both the rate limit and block record
    delete_result = await db.rate_limits.delete_many({
        "key": {"$in": [key, block_key]}
    })
    
    print(f"Deleted {delete_result.deleted_count} rate limit/block records!")


if __name__ == "__main__":
    asyncio.run(clear_rate_limits())
