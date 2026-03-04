import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import verify_password
from app.models.user import User
from sqlalchemy import select

async def debug_login():
    email = "admin@syyaimeiq.com"
    password = "admin1234"

    async with AsyncSessionLocal() as db:
        # Step 1: set tenant schema
        print("Step 1: Setting search_path to tenant_demo")
        await db.execute(text("SET search_path TO tenant_demo"))

        # Step 2: find user
        print("Step 2: Looking up user by email")
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print("FAIL: User not found via ORM")
            # Try raw SQL
            r2 = await db.execute(text("SELECT id, email, hashed_password, is_active FROM users WHERE email = :e"), {"e": email})
            row = r2.fetchone()
            if row:
                print("BUT found via raw SQL:", row.email)
            else:
                print("Not found via raw SQL either")
            return

        print("Step 3: User found:", user.email, "active:", user.is_active)

        # Step 4: verify password
        print("Step 4: Verifying password")
        ok = verify_password(password, user.hashed_password)
        print("Password match:", ok)

        if not ok:
            print("FAIL: Password mismatch")
            print("Hash:", repr(user.hashed_password))

asyncio.run(debug_login())
