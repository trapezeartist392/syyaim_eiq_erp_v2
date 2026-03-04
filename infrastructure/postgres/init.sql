-- ManufactureIQ ERP — PostgreSQL Initialization
-- Runs once when the postgres container first starts

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fast text search

-- Seed data will be inserted by the backend on first startup
-- (via Alembic migrations + seed script)

-- Grant permissions
-- Permissions are handled by the POSTGRES_USER environment variable
