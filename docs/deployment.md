# Deploying Aquabely on a Home NAS

## Architecture

```
Internet → Router (port forward) → NAS
           80  → 8080               ├── Caddy (host 8080/8443 → container 80/443)
           443 → 8443               │     • HTTPS via Let's Encrypt
                                    │     • Import page: password-protected
                                    │     • Dashboards: public
                                    └── App container (port 8504)
                                          • aquabely-data volume  ← SQLite DB
                                          • aquabely-inbox volume ← PDF uploads
```

## Deployment files

| File | Purpose |
|------|---------|
| `Dockerfile` | Builds the app image |
| `docker-compose.yml` | Runs the app + Caddy together |
| `Caddyfile` | Reverse proxy: HTTPS, auth on Import page |
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

The Import page requires a password. Caddy stores it hashed.

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

### Step 8 — (Optional) Migrate an existing database

If you already have data in a local `aquabely.db`, copy it into the Docker volume before first start:

```sh
docker volume create aquabely_aquabely-data
docker run --rm \
  -v aquabely_aquabely-data:/data \
  -v $(pwd):/src \
  alpine cp /src/aquabely.db /data/aquabely.db
```

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
| `https://rookie-raspbi.cz` | Athletes dashboard loads |
| `https://rookie-raspbi.cz/Import` | Browser prompts for username/password |

---

## Day-to-day operations

### Adding PDFs to import

PDFs live in the `aquabely-inbox` Docker volume. Copy a file in from the NAS host:

```sh
docker run --rm \
  -v aquabely_aquabely-inbox:/inbox \
  -v /path/to/your/pdfs:/src \
  alpine cp /src/result.pdf /inbox/result.pdf
```

Then open `https://rookie-raspbi.cz/Import` in the browser and click **Import**.

> If your NAS has a file manager that can browse Docker volumes (e.g. Portainer), you can drag and drop files there instead.

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
