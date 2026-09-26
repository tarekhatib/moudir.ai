# Moudir dashboard

React 19 + TypeScript manager dashboard, built with Vite.

```bash
npm install
npm run dev      # http://localhost:5173, proxies /api to the backend on :8000
npm run lint     # oxlint
npm run build    # type-check and build to dist/
```

The app always calls the API at the same origin under `/api`, so the session cookie is
first-party:

- **Development:** Vite proxies `/api` to `http://localhost:8000` (override with
  `VITE_BACKEND_URL`).
- **Production:** Caddy serves `dist/` and proxies `/api` to the backend (see the
  [Dockerfile](Dockerfile), [Caddyfile](Caddyfile) and [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)).

`VITE_API_URL` can point the app at an API on another origin, but then the backend needs
that origin in `CORS_ORIGINS` and cross-site cookies, which browsers increasingly block —
prefer the proxy.

## Layout

- `src/Root.tsx` — checks the session and shows sign-in or the app; returns to sign-in on `401`.
- `src/App.tsx` — shell, navigation and employee pages.
- `src/components/` — team overview, report, trends, settings, desktop agent, account.
- `src/api/client.ts` — the one place that talks to the backend.
