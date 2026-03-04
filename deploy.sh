#!/bin/bash
set -e

echo "========================================"
echo " Syyaim EIQ ERP — Deploy Script"
echo "========================================"

# Check .env
if [ ! -f .env ]; then
  echo "Creating .env from template..."
  cp .env.example .env
  echo ""
  echo "  IMPORTANT: Edit .env and set:"
  echo "    ANTHROPIC_API_KEY=sk-ant-..."
  echo "    POSTGRES_PASSWORD=<strong password>"
  echo "    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
  echo ""
  read -p "Press ENTER after editing .env to continue..."
fi

echo "Building and starting services..."
docker compose pull postgres nginx 2>/dev/null || true
docker compose build --parallel
docker compose up -d

echo "Waiting for database..."
sleep 8

echo "Running seed data..."
docker compose exec -T backend python /app/scripts/seed.py 2>/dev/null || \
  echo "  (Seed skipped — run manually if needed: docker compose exec backend python /app/scripts/seed.py)"

echo ""
echo "========================================"
echo "  Syyaim EIQ ERP is ready!"
echo "========================================"
echo "  URL:      http://localhost"
echo "  API docs: http://localhost/api/docs"
echo "  Login:    admin@syyaimeiq.com"
echo "  Password: Admin@123"
echo ""
echo "  NOTE: Change the default password!"
echo "========================================"
