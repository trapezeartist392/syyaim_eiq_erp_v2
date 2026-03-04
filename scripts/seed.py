#!/usr/bin/env python3
"""
Syyaim EIQ ERP — Database Seed Script
Run after first boot to create admin user and sample data.
Usage: docker compose exec backend python scripts/seed.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# Also add /app for Docker container context
sys.path.insert(0, "/app")
try:
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
except OSError:
    pass

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.crm import Lead, LeadStatus, SalesOrder
from app.models.purchase import Vendor, PurchaseRequisition, PurchaseOrder
from app.models.material import Item, ItemCategory
from app.models.hr import Employee, EmploymentType
from app.models.finance import Account, AccountType
from sqlalchemy import select
from datetime import date


async def seed():
    print("🌱 Seeding Syyaim EIQ ERP database...")

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(
            select(User).where(User.email == "admin@syyaimeiq.com")
        )
        if result.scalar_one_or_none():
            print("Seed data already exists. Skipping.")
            return

        # ── Admin User ────────────────────────────────────────
        admin = User(
            email="admin@syyaimeiq.com",
            full_name="System Administrator",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            department="IT",
            is_active=True,
        )
        db.add(admin)

        # ── Sample Vendors ────────────────────────────────────
        vendors = [
            Vendor(
                code="VEND001", name="Reliable Steel Traders",
                email="sales@reliablesteel.com", phone="9123456789",
                gstin="27BBBBB0000B1Z5", payment_terms=30, rating=4.5,
            ),
            Vendor(
                code="VEND002", name="Prime Packaging Co",
                email="info@primepack.com", phone="9123456790",
                payment_terms=15, rating=3.8,
            ),
            Vendor(
                code="VEND003", name="Tech Components India",
                email="supply@techcomp.in", phone="9123456791",
                payment_terms=45, rating=4.8,
            ),
        ]
        for v in vendors:
            db.add(v)

        # ── Sample Inventory Items ────────────────────────────
        items = [
            Item(
                code="RM-001", name="Steel Sheet 2mm",
                category=ItemCategory.RAW_MATERIAL, unit="KG",
                current_stock=1200, reorder_point=500, reorder_qty=2000,
                unit_cost=85.0, location="Warehouse A",
            ),
            Item(
                code="RM-002", name="Aluminium Extrusion 50x50",
                category=ItemCategory.RAW_MATERIAL, unit="MTR",
                current_stock=80, reorder_point=100, reorder_qty=500,
                unit_cost=320.0, location="Warehouse A",
            ),
            Item(
                code="FG-001", name="Precision Gear Assembly",
                category=ItemCategory.FINISHED_GOODS, unit="PCS",
                current_stock=150, reorder_point=50, reorder_qty=200,
                unit_cost=1200.0, location="Warehouse B",
            ),
            Item(
                code="FG-002", name="Motor Housing Unit",
                category=ItemCategory.FINISHED_GOODS, unit="PCS",
                current_stock=15, reorder_point=20, reorder_qty=100,
                unit_cost=3500.0, location="Warehouse B",
            ),
            Item(
                code="CON-001", name="Corrugated Box 30x20x15",
                category=ItemCategory.CONSUMABLES, unit="PCS",
                current_stock=3000, reorder_point=1000, reorder_qty=5000,
                unit_cost=18.0, location="Warehouse C",
            ),
        ]
        for i in items:
            db.add(i)

        # ── Sample Leads ──────────────────────────────────────
        leads = [
            Lead(
                company_name="Bharat Auto Parts Ltd",
                contact_name="Vikram Singh", email="vikram@bharatauto.com",
                phone="9876543210", source="website", status=LeadStatus.QUALIFIED,
                value=500000, ai_score=78,
                ai_notes="Strong manufacturing fit, large fleet.",
            ),
            Lead(
                company_name="Sunrise Textile Mills",
                contact_name="Meera Patel", email="meera@sunrisetex.com",
                phone="9876543211", source="referral", status=LeadStatus.NEW,
                value=300000, ai_score=0,
            ),
        ]
        for l in leads:
            db.add(l)

        # ── Sample Employees ──────────────────────────────────
        employees = [
            Employee(
                employee_id="EMP001", full_name="Rajesh Kumar",
                email="rajesh.kumar@company.com", phone="9811223344",
                department="Production", designation="Production Manager",
                employment_type=EmploymentType.FULL_TIME,
                date_of_joining=date(2020, 4, 1),
                basic_salary=55000, hra=22000, allowances=8000,
                pf_applicable=True, esi_applicable=False,
            ),
            Employee(
                employee_id="EMP002", full_name="Priya Sharma",
                email="priya.sharma@company.com", phone="9811223345",
                department="Finance", designation="Senior Accountant",
                employment_type=EmploymentType.FULL_TIME,
                date_of_joining=date(2021, 7, 15),
                basic_salary=45000, hra=18000, allowances=7000,
                pf_applicable=True, esi_applicable=False,
            ),
            Employee(
                employee_id="EMP003", full_name="Amit Patel",
                email="amit.patel@company.com", phone="9811223346",
                department="Purchase", designation="Purchase Executive",
                employment_type=EmploymentType.FULL_TIME,
                date_of_joining=date(2022, 1, 10),
                basic_salary=35000, hra=14000, allowances=5000,
                pf_applicable=True, esi_applicable=True,
            ),
        ]
        for e in employees:
            db.add(e)

        # ── Chart of Accounts ─────────────────────────────────
        accounts = [
            Account(code="1000", name="Cash & Bank", account_type=AccountType.ASSET, balance=500000),
            Account(code="1200", name="Accounts Receivable", account_type=AccountType.ASSET, balance=280000),
            Account(code="1300", name="Inventory", account_type=AccountType.ASSET, balance=850000),
            Account(code="2100", name="Accounts Payable", account_type=AccountType.LIABILITY, balance=320000),
            Account(code="2200", name="Salary Payable", account_type=AccountType.LIABILITY, balance=0),
            Account(code="3000", name="Share Capital", account_type=AccountType.EQUITY, balance=1000000),
            Account(code="4000", name="Sales Revenue", account_type=AccountType.INCOME, balance=1500000),
            Account(code="4100", name="Other Income", account_type=AccountType.INCOME, balance=50000),
            Account(code="5000", name="Cost of Goods Sold", account_type=AccountType.EXPENSE, balance=900000),
            Account(code="5100", name="Salaries & Wages", account_type=AccountType.EXPENSE, balance=400000),
            Account(code="6000", name="Office & Admin", account_type=AccountType.EXPENSE, balance=120000),
            Account(code="7000", name="Manufacturing Overhead", account_type=AccountType.EXPENSE, balance=80000),
        ]
        for a in accounts:
            db.add(a)

        await db.commit()

    print("✅ Seed completed!")
    print("\n🔑 Default Login:")
    print("   Email   : admin@syyaimeiq.com")
    print("   Password: Admin@123")
    print("\n⚠️  Change the default password immediately in production!")


if __name__ == "__main__":
    asyncio.run(seed())
