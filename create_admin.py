import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password

async def create():
    async with AsyncSessionLocal() as db:
        await db.execute(text("SET search_path TO tenant_demo"))
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'staff',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """))
        await db.execute(text("""
            INSERT INTO users (email, full_name, hashed_password, role, is_active)
            VALUES (:email, :name, :pwd, :role, true)
            ON CONFLICT DO NOTHING
        """), {
            "email": "admin@syyaimeiq.com",
            "name": "Admin",
            "pwd": hash_password("admin1234"),
            "role": "admin"
        })
        await db.commit()
        print("Admin user created successfully")

asyncio.run(create())
