# Deploy AVTOMOD

## Local upload

```bash
cd /Users/yura/Documents/auto_repair

rsync -az --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".env" \
  --exclude "db.sqlite3" \
  --exclude "data" \
  --exclude "media" \
  --exclude "staticfiles" \
  --exclude "__pycache__" \
  --exclude ".DS_Store" \
  -e "ssh -i ~/.ssh/tehsfera_ci" \
  ./ deploy@45.128.205.77:/home/deploy/avtomod/
```

## First server start

```bash
ssh -i ~/.ssh/tehsfera_ci deploy@45.128.205.77

cd /home/deploy/avtomod
cp .env.example .env
nano .env

docker compose up -d --build
docker compose logs -f web
```

If the server uses the old compose command:

```bash
docker-compose up -d --build
docker-compose logs -f web
```

## Caddy

```bash
sudo nano /etc/caddy/Caddyfile
```

Add the block from:

```bash
/home/deploy/avtomod/deploy/Caddyfile.avtomod.by
```

Then reload Caddy:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```
## Admin user

```bash
docker compose exec web python manage.py createsuperuser
```

Or for old compose:

```bash
docker-compose exec web python manage.py createsuperuser
```

## Update after changes

```bash
cd /Users/yura/Documents/auto_repair

rsync -az --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".env" \
  --exclude "db.sqlite3" \
  --exclude "data" \
  --exclude "media" \
  --exclude "staticfiles" \
  --exclude "__pycache__" \
  --exclude ".DS_Store" \
  -e "ssh -i ~/.ssh/tehsfera_ci" \
  ./ deploy@45.128.205.77:/home/deploy/avtomod/

ssh -i ~/.ssh/tehsfera_ci deploy@45.128.205.77
cd /home/deploy/avtomod
docker compose up -d --build
```
