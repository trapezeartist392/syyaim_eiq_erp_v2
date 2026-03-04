import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, verify_password

async def fix():
    h = hash_password("admin1234")
    async with AsyncSessionLocal() as db:
        await db.execute(text("SET search_path TO tenant_demo"))
        await db.execute(
            text("UPDATE users SET hashed_password = :h WHERE email = :e"),
            {"h": h, "e": "admin@syyaimeiq.com"}
        )
        await db.commit()
        result = await db.execute(
            text("SELECT hashed_password FROM users WHERE email = :e"),
            {"e": "admin@syyaimeiq.com"}
        )
        saved = result.fetchone().hashed_password
        print("Saved hash:", repr(saved))
        print("Verify:", verify_password("admin1234", saved))
        print("Done — try logging in now")

asyncio.run(fix())
