@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Syyaim EIQ ERP - Deploy Script
echo ========================================

:: Check .env
if not exist ".env" (
    echo Creating .env from template...
    copy ".env.example" ".env" >nul

    echo.
    echo   IMPORTANT: Edit .env and set:
    echo     ANTHROPIC_API_KEY=sk-ant-...
    echo     POSTGRES_PASSWORD=^<strong password^>
    echo     SECRET_KEY=^<random 64 char string^>
    echo.
    start /wait notepad ".env"
    echo Press ENTER after editing .env to continue...
    pause >nul
)

echo Building and starting services...
docker compose pull postgres nginx >nul 2>&1
docker compose build --parallel
docker compose up -d

echo Waiting for database...
timeout /t 8 /nobreak >nul

echo Running seed data...
docker compose exec -T backend python /app/scripts/seed.py >nul 2>&1
if %errorlevel% neq 0 (
    echo   ^(Seed skipped - run manually if needed: docker compose exec backend python /app/scripts/seed.py^)
)

echo.
echo ========================================
echo   Syyaim EIQ ERP is ready!
echo ========================================
echo   URL:      http://localhost
echo   API docs: http://localhost/api/docs
echo   Login:    admin@syyaimeiq.com
echo   Password: Admin@123
echo.
echo   NOTE: Change the default password!
echo ========================================
pause
