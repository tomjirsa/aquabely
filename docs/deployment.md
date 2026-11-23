# Deploying Aquabely on a Home NAS

## Architecture

```
Internet → Router (port forward) → NAS
           80  → 8080               ├── Caddy (host 8080/8443 → container 80/445)
           443 → 8443               │     • HTTPS via Let's Encrypt
                                    │     • Whole site behind basic auth
                                    └── App container (FastAPI, port 8000)
                                          • serves /api and the built React app
                                          • aquabely-data volume  ← SQLite DB
                                          • aquabely-inbox volume ← PDF uploads
```

## Deployment files

| File | Purpose |
|------|---------|
| `Dockerfile` | Two-stage build: Node 24 builds the React app (`web/dist`), then a Python 3.12 image runs FastAPI with uvicorn on port 8000 and serves the built app |
| `docker-compose.yml` | Runs the app + Caddy together |
| `Caddyfile` | Reverse proxy: HTTPS, basic auth on the whole site |
| `.env.example` | Template for required environment variables |

---

## Step-by-step deployment

### Step 1 — Find your NAS's local IP

You need the NAS's fixed local IP address for router port forwarding.

On the NAS terminal:
```sh
ip addr show | grep "inet "
# or
hostname -I
```

Note the IP (e.g. `192.168.1.100`). Set a static IP or DHCP reservation for it in your router so it never changes.

---

### Step 2 — Set up DuckDNS (free dynamic DNS)

Your home internet connection likely has a dynamic public IP that changes periodically. DuckDNS gives you a stable hostname that always points to your current IP.

1. Go to [duckdns.org](https://www.duckdns.org) and log in with a Google/GitHub account.
2. Create a subdomain, e.g. `aquabely` → you get `rookie-raspbi.cz`.
3. Set up automatic IP updates on the NAS so the record stays current:

   **Option A — most NAS OS have a built-in DDNS client** (Synology, QNAP, etc.):
   - Go to Control Panel → External Access → DDNS → Add → select DuckDNS.

   **Option B — cron job:**
   ```sh
   # Replace TOKEN and DOMAIN with your values
   echo "*/5 * * * * curl -s 'https://www.duckdns.org/update?domains=aquabely&token=YOUR_TOKEN&ip=' > /dev/null" | crontab -
   ```

---

### Step 3 — Forward ports on your router

Log in to your router admin panel (usually `192.168.1.1` or `192.168.0.1`) and add two port forwarding rules:

| External port | Internal IP | Internal port | Protocol |
|---------------|-------------|---------------|----------|
| 80 | 192.168.1.100 | 8080 | TCP |
| 443 | 192.168.1.100 | 8443 | TCP |

> Caddy binds to host ports **8080/8443** to avoid conflicts with other services already using 80/443 on the NAS. The router forwards standard ports from the internet to these, so Let's Encrypt and HTTPS work normally.

---

### Step 4 — Install Docker on the NAS

**Synology:** Package Center → search Docker → Install.

**QNAP:** App Center → search Container Station → Install.

**Generic Linux NAS:**
```sh
curl -fsSL https://get.docker.com | sh
```

Verify:
```sh
docker --version
docker compose version
```

---

### Step 5 — Copy the app to the NAS

**Option A — Git (recommended):**
```sh
ssh user@192.168.1.100
git clone https://github.com/youruser/aquabely.git
cd aquabely
```

**Option B — SCP from your Mac:**
```sh
scp -r /Users/tjirsik/Repository/aquabely user@192.168.1.100:~/aquabely
```

---

### Step 6 — Generate the admin password hash

The whole site requires a password (Caddy basic auth). Caddy stores it hashed.

Run this on the NAS and type your chosen password when prompted:
```sh
docker run --rm -it caddy:2-alpine caddy hash-password
```

Copy the output — it looks like `$2a$14$abc123...`.

---

### Step 7 — Create the `.env` file

```sh
cd ~/aquabely
cp .env.example .env
nano .env   # or vi, or any editor
```

Fill in your values:
```env
DOMAIN=rookie-raspbi.cz
AUTH_USER=admin
AUTH_HASH=$2a$14$...
```

> **Important:** The `$` characters in `AUTH_HASH` must not be interpreted by the shell. Save them as-is in the `.env` file — Docker Compose reads it literally.

---

### Step 8 — Existing database

This release does not change the database. Keep the existing aquabely-data volume; the app opens the existing database and applies the schema on start.

---

### Step 9 — Start the app

```sh
docker compose --env-file .env up -d
```

Docker will:
1. Build the app image (~2 min on first run)
2. Pull the Caddy image
3. Start both containers
4. Caddy will automatically obtain a TLS certificate from Let's Encrypt (requires port 80 to be reachable from the internet)

Check that both containers are running:
```sh
docker compose ps
```

Check Caddy logs to confirm the certificate was issued:
```sh
docker compose logs caddy
# Look for: certificate obtained successfully
```

The app is now live at `https://rookie-raspbi.cz`.

---

### Step 10 — Verify

| URL | Expected |
|-----|----------|
| `https://rookie-raspbi.cz` | Browser prompts for username/password, then the home page loads |
| `https://rookie-raspbi.cz/import` | Same login applies (every page is protected) |
| `https://rookie-raspbi.cz/api/health` | `{"status":"ok"}` |

The old paths `/Import`, `/Competitions`, `/Athletes`, `/Clubs` and `/Figures` redirect (301) to their lowercase routes.

---

## Running locally (without Docker)

The API and the React app run as two processes during development.

```sh
# Terminal 1: API on http://localhost:8000
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Terminal 2: React dev server on http://localhost:5173 (proxies /api to port 8000)
cd web
npm ci
npm run dev
```

To serve the built app from FastAPI alone, run `npm run build` in `web/` and start uvicorn. It serves `web/dist` for every non-API path, the same way the container does. Set `AQUABELY_DB` and `AQUABELY_INBOX` to choose where the database and uploads live.

Tests: `python -m pytest -q` for the API, `npm test` in `web/` for the frontend.

---

## Day-to-day operations

### Adding PDFs to import

Upload PDFs on the Import page. The inbox is used only to store uploads.

### Updating the app

```sh
cd ~/aquabely
git pull
docker compose --env-file .env up -d --build
```

The database and inbox volumes are untouched by rebuilds.

### Viewing logs

```sh
docker compose logs -f app     # app logs
docker compose logs -f caddy   # proxy / HTTPS logs
```

### Stopping

```sh
docker compose down
```

Data is preserved in the volumes. To also wipe all data:
```sh
docker compose down -v
```

### Backup

Back up the SQLite database by copying it out of the volume:

```sh
docker run --rm \
  -v aquabely_aquabely-data:/data \
  -v $(pwd):/backup \
  alpine cp /data/aquabely.db /backup/aquabely-$(date +%Y%m%d).db
```
