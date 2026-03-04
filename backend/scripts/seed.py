#!/usr/bin/env python3
"""
Syyaim EIQ ERP - Database Seed Script
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


async def seed():
    print("Seeding Syyaim EIQ ERP database...")

    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(
            select(User).where(User.email == "admin@syyaimeiq.com")
        )
        if result.scalar_one_or_none():
            print("Admin user already exists - skipping.")
            return

        admin = User(
            email="admin@syyaimeiq.com",
            full_name="System Administrator",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.ADMIN,
            department="IT",
            is_active=True,
        )
        db.add(admin)
        await db.commit()

    print("Seed completed!")
    print("")
    print("  Login:    admin@syyaimeiq.com")
    print("  Password: Admin@123")
    print("")
    print("  WARNING: Change the default password immediately!")


if __name__ == "__main__":
    asyncio.run(seed())
