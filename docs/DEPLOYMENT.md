# Deploying Moudir.ai

The recommended setup is a single Linux server running [docker-compose.yml](../docker-compose.yml):

| Service | Image | Role |
| :--- | :--- | :--- |
| `web` | `dashboard/Dockerfile` (Caddy) | Serves the dashboard, proxies `/api/*` to the backend, gets and renews HTTPS certificates automatically |
| `backend` | `backend/Dockerfile` | FastAPI app; applies database migrations on start |
| `db` | `postgres:16-alpine` | Data, in the `db-data` volume |

The dashboard and API share one origin (`https://your-domain` and `https://your-domain/api`), so
sign-in uses a first-party `HttpOnly; Secure; SameSite=Lax` cookie and no CORS is needed.

## 1. Prepare a server

- Any VPS with Docker and the Compose plugin (e.g. 2 vCPU / 2 GB RAM to start).
- A domain (e.g. `moudir.example.com`) with an **A/AAAA record pointing at the server**.
- Ports **80 and 443** open. Caddy needs both to obtain the certificate.

## 2. Configure and start

```bash
git clone <this repo> moudir && cd moudir
cp .env.example .env
```

Edit `.env`:

| Variable | Value |
| :--- | :--- |
| `DOMAIN` | Your hostname, e.g. `moudir.example.com` |
| `POSTGRES_PASSWORD` | A long random value: `openssl rand -base64 32` |
| `ALLOW_SIGNUP` | `true` to let companies create accounts; `false` to close sign-up |

```bash
docker compose up -d --build
docker compose logs -f backend     # watch migrations run and the server start
```

Open `https://<DOMAIN>`, click **Create a company account**, and you're the owner of the first
organization. If you'll onboard customers yourself, set `ALLOW_SIGNUP=false` afterwards and
`docker compose up -d`.

## 3. Connect employees' agents

For each employee: **Employees → (employee) → Desktop agent → Generate token**, then follow
[agent/README.md](../agent/README.md). The agent's `BACKEND_URL` is `https://<DOMAIN>/api`.

## Operating it

**Upgrades**

```bash
git pull
docker compose up -d --build       # migrations apply automatically on backend start
```

**Backups** — the only state is the Postgres volume. Schedule a daily dump off the server:

```bash
docker compose exec -T db pg_dump -U moudir -Fc moudir > moudir-$(date +%F).dump
# restore: docker compose exec -T db pg_restore -U moudir -d moudir --clean < moudir-YYYY-MM-DD.dump
```

**Logs** — `docker compose logs backend` (plain text, one line per event; failed sign-ins and
rejected agent events are logged at INFO/WARNING).

**Health** — `https://<DOMAIN>/api/health` returns `{"status":"ok"}` when the API can reach the
database. Point your uptime monitor at it.

## Backend configuration reference

Set these on the `backend` service (compose already sets the first three).

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | `production` hides `/docs` and forces Secure cookies |
| `DATABASE_URL` | `sqlite:///./data/moudir.db` | `postgresql://…` in production (`postgres://` is accepted) |
| `CORS_ORIGINS` | `http://localhost:5173,…` | Comma-separated origins allowed cross-origin; empty when same-origin |
| `ALLOW_SIGNUP` | `true` | Whether new organizations can sign up |
| `SESSION_TTL_HOURS` | `336` | How long a dashboard sign-in lasts (14 days) |
| `COOKIE_SECURE` | auto | Override the Secure cookie flag (defaults to on in production) |
| `MAX_INGEST_EVENTS` | `1000` | Largest event batch an agent may send |
| `LOGIN_MAX_FAILURES` / `LOGIN_WINDOW_MINUTES` | `10` / `15` | Sign-in rate limit per email and per IP |
| `WEB_CONCURRENCY` | `2` | Uvicorn worker processes |
| `LOG_LEVEL` | `INFO` | Python log level |

## Alternative: Vercel + a hosted backend

If you'd rather not run a server for the dashboard:

1. Deploy `backend/` (it has a Dockerfile) to Render, Railway or Fly.io with a managed
   Postgres, and set `ENVIRONMENT=production`, `DATABASE_URL`, `CORS_ORIGINS=` (empty).
2. Deploy `dashboard/` to Vercel (framework preset: Vite), and add `dashboard/vercel.json` so
   `/api` stays same-origin — this keeps the session cookie first-party:

   ```json
   {
     "rewrites": [
       { "source": "/api/:path*", "destination": "https://YOUR-BACKEND-HOST/:path*" },
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```

3. Agents use `BACKEND_URL=https://<your-vercel-domain>/api`.

Because requests reach the backend through Vercel's proxy, set the backend's trusted proxy
IPs (`--forwarded-allow-ips`) to your platform's documented ranges so sign-in rate limiting
sees real client IPs.
