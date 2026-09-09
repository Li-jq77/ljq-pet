#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if [[ ! -f manage.py || ! -f requirements.txt ]]; then
    echo "ERROR: deploy/setup_server.sh must run from the project root." >&2
    exit 1
fi

echo "[1/8] Installing system packages"
sudo apt update
sudo apt install -y python3-venv python3-pip nginx mysql-server unzip

echo "[2/8] Creating Python virtual environment"
if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "[3/8] Checking .env"
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo ""
    echo "Created .env from .env.example."
    echo "Edit it first, then run this script again:"
    echo "  nano .env"
    exit 1
fi

if grep -qE '^(DJANGO_SECRET_KEY|DB_PASSWORD)=change-me$' .env; then
    echo "ERROR: DJANGO_SECRET_KEY or DB_PASSWORD still has the placeholder." >&2
    echo "Edit .env, then run this script again." >&2
    exit 1
fi

set -a
source .env
set +a

echo "[4/8] Applying database migrations and collecting static files"
mkdir -p media
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput

echo "[5/8] Setting file ownership"
sudo chown -R www-data:www-data "$APP_DIR"
sudo chmod 600 "$APP_DIR/.env"

echo "[6/8] Installing Gunicorn systemd service"
sudo cp deploy/pet-agent.service /etc/systemd/system/pet-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now pet-agent

echo "[7/8] Installing Nginx site"
sudo cp deploy/nginx-pet-agent.conf /etc/nginx/sites-available/pet-agent
sudo ln -sf /etc/nginx/sites-available/pet-agent /etc/nginx/sites-enabled/pet-agent
sudo nginx -t
sudo systemctl reload nginx

echo "[8/8] Verifying service"
sudo systemctl status pet-agent --no-pager || true
curl -I http://127.0.0.1/

echo ""
echo "Deployment script finished."
echo "Next: open ports 80 and 443 in the cloud security group, then check:"
echo "  curl -I http://8.217.93.123/"
