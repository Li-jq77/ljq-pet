# Pet Agent deployment on Ubuntu (Alibaba Cloud)

This is a Django project and should run behind Gunicorn and Nginx:

    Nginx (port 80) -> Gunicorn (127.0.0.1:8000) -> Django + MySQL

MySQL environment variables are named `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST`, and `DB_PORT`; see `.env.example`.

After the MySQL database, user, and `.env` are ready, the remaining server
steps can be run with one script:

```bash
bash deploy/setup_server.sh
```

The detailed manual steps below match what the script does.

## 1. Install system packages

```bash
sudo apt update
sudo apt install -y python3.12-venv nginx mysql-server unzip
```

## 2. Put the project on the server

```bash
sudo mkdir -p /opt/pet-agent
cd /opt/pet-agent
# Upload/extract the project files into this directory.
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3. Create the MySQL database and user

```bash
sudo mysql <<'SQL'
CREATE DATABASE pet_agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'pet_agent'@'localhost' IDENTIFIED BY 'REPLACE_WITH_PASSWORD';
GRANT ALL PRIVILEGES ON pet_agent_db.* TO 'pet_agent'@'localhost';
FLUSH PRIVILEGES;
SQL
```

## 4. Create `.env`

```bash
cp .env.example .env
nano .env
```

Generate a secret key with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Put that value in `DJANGO_SECRET_KEY` and put the same MySQL password from the
step above in `DB_PASSWORD`.

## 5. Migrate and collect static files

```bash
set -a; source .env; set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
mkdir -p media
```

Optional: `data.json` contains demo users/products. Do not run `loaddata
data.json` directly because it contains `auth.permission`,
`contenttypes.contenttype`, and `sessions.session` records that conflict with a
fresh migrated database. Filter those models out first:

```bash
.venv/bin/python - <<'PY'
import json

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

skip = {"auth.permission", "contenttypes.contenttype", "sessions.session"}
clean = [item for item in data if item["model"] not in skip]

with open("seed_data.json", "w", encoding="utf-8") as f:
    json.dump(clean, f, ensure_ascii=False, indent=2)
PY
.venv/bin/python manage.py loaddata seed_data.json
.venv/bin/python manage.py changepassword admin
```

## 6. Give www-data access and start the service

```bash
sudo chown -R www-data:www-data /opt/pet-agent
sudo chmod 600 /opt/pet-agent/.env
sudo cp deploy/pet-agent.service /etc/systemd/system/pet-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now pet-agent
sudo systemctl status pet-agent
```

## 7. Configure Nginx

```bash
sudo cp deploy/nginx-pet-agent.conf /etc/nginx/sites-available/pet-agent
sudo ln -sf /etc/nginx/sites-available/pet-agent /etc/nginx/sites-enabled/pet-agent
sudo nginx -t
sudo systemctl reload nginx
```

Also open ports 80 and 443 in the Alibaba Cloud security group/firewall.

## 8. Verify

```bash
curl -I http://127.0.0.1/
curl -I http://8.217.93.123/
journalctl -u pet-agent -n 50 --no-pager
```

If you add a domain later, point an A record to `8.217.93.123`, add the domain
to `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` in `.env`, then use
`certbot --nginx` to enable HTTPS.
