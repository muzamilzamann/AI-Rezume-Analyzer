# Deployment Guide

This project deploys as three independent pieces:

| Component | Host           | Config file              |
| --------- | -------------- | ------------------------ |
| Database  | Neon           | — (managed Postgres)     |
| Backend   | Render *or* Railway | `render.yaml` / `railway.json` |
| Frontend  | Vercel         | `frontend/vercel.json`   |

The backend is shipped as a Docker image (built from `docker/backend.Dockerfile`).
The Dockerfile runs Alembic migrations on every startup and binds to `$PORT`,
so it works on Render, Railway, and `docker-compose` without changes.

---

## Prerequisites

- A [Neon](https://neon.tech) PostgreSQL project (free tier) + its connection string.
- Accounts on the hosts you plan to use:
  - [Vercel](https://vercel.com) (frontend)
  - [Render](https://render.com) **or** [Railway](https://railway.com) (backend)
- The repo pushed to GitHub (Render, Railway, and Vercel all deploy from a Git branch).

---

## 1. Database (Neon)

1. Create a Neon project and copy the connection string. It looks like:
   ```
   postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require
   ```
2. Keep this handy — both the backend and migrations read it from `DATABASE_URL`.
   The backend auto-normalizes the URL for asyncpg, so paste it verbatim.

> The schema is created by migrations — no manual SQL is needed.

---

## 2. Backend

Pick **one** of the following. Both build the same Docker image.

### Option A — Render (recommended, uses `render.yaml`)

1. Push the repo to GitHub.
2. In the Render dashboard: **New → Blueprint**, select your repo.
   Render detects `render.yaml` and creates a `resume-analyzer-backend` web service.
3. During the first sync you are prompted for the `sync: false` secrets. Provide:
   - `DATABASE_URL` — your Neon connection string.
   - `FRONTEND_URL` — leave for now; set it to your Vercel URL after step 3
     (it enables CORS so the browser can call the API).
   - `GEMINI_API_KEY` *(optional)* — enables AI feedback; blank = rule-based fallback.
   - `CLOUDINARY_*` *(optional)* — see *Persistent uploads* below.
   - `JWT_SECRET_KEY` is **auto-generated** by Render (`generateValue: true`).
4. Deploy. Render runs the Docker build, then migrations + `uvicorn` on `$PORT`.
5. Confirm `https://resume-analyzer-backend.onrender.com/health` returns `{"status":"ok"}`.

`BACKEND_BASE_URL` is wired automatically from Render's `RENDER_EXTERNAL_URL`.

### Option B — Railway (uses `railway.json`)

1. Push the repo to GitHub.
2. In Railway: **New Project → Deploy from GitHub repo**.
3. Railway reads `railway.json` and builds `docker/backend.Dockerfile`
   (repo root is the build context). The health check targets `/health`.
4. In the service **Variables** tab, add (all required except where noted):
   - `DATABASE_URL` — Neon connection string.
   - `JWT_SECRET_KEY` — generate a strong secret (see below).
   - `DB_SSL_MODE` — `require`
   - `FRONTEND_URL` — your Vercel URL (set after step 3).
   - `BACKEND_BASE_URL` — your Railway public URL (find it under **Settings → Networking**).
   - `GEMINI_API_KEY` *(optional)*
   - `CLOUDINARY_*` *(optional)*
5. Deploy and confirm `/health` responds.

Generate a JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 3. Frontend (Vercel)

1. In Vercel: **Add New → Project**, import the GitHub repo.
2. Set **Root Directory** to `frontend/`. Vercel auto-detects Vite and reads
   `frontend/vercel.json` (build command `npm run build`, output `dist`, SPA fallback).
3. Add an environment variable **before the first build** (Project → Settings → Environment Variables):
   - `VITE_API_URL` — the absolute backend API URL, including the `/api/v1` prefix.
     - Render: `https://resume-analyzer-backend.onrender.com/api/v1`
     - Railway: `https://<your-service>.up.railway.app/api/v1`
4. Deploy. Vercel builds the SPA and serves it with client-side routing enabled.

---

## 4. Connect frontend ↔ backend (CORS)

The backend only allows requests from `FRONTEND_URL`. After the frontend is live:

1. Copy your Vercel URL (e.g. `https://your-app.vercel.app`) — no trailing slash.
2. Set it as `FRONTEND_URL` on the backend (Render: Environment tab; Railway: Variables).
3. Trigger a redeploy (or wait for auto-deploy).

That's it — register a user, upload a resume, and run an analysis end to end.

---

## Persistent uploads (important)

Render and Railway have **ephemeral filesystems**: any file written at runtime is
lost on redeploy. Resumes uploaded via the local-storage fallback would disappear.

Recommended fixes (pick one):

- **Cloudinary (recommended).** Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`,
  and `CLOUDINARY_API_SECRET` on the backend. The app then stores all resumes in
  Cloudinary and nothing is kept on disk.
- **Render persistent disk** (paid plan). Attach a disk mounted at `/app/uploads`
  to the backend service.

---

## Local Docker (optional)

Run the whole stack locally without touching the cloud:

```bash
cp backend/.env.example backend/.env      # fill DATABASE_URL + JWT_SECRET_KEY
docker compose up --build
```

The frontend is served by nginx on `http://localhost:5173` and proxies
`/api` and `/uploads` to the backend on port 8000.

---

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:

- **Backend** — `ruff check` + `pytest`
- **Frontend** — `oxlint` + `vite build`
- **Docker** — builds both images to catch Dockerfile regressions

Render, Railway, and Vercel each auto-deploy on pushes to `main` once connected.

---

## Environment variables reference

### Backend

| Variable            | Required | Notes                                                  |
| ------------------- | -------- | ------------------------------------------------------ |
| `DATABASE_URL`      | yes      | Neon connection string (auto-normalized for asyncpg)   |
| `JWT_SECRET_KEY`    | yes      | Long random string (auto-generated on Render)          |
| `DB_SSL_MODE`       | yes      | `require` for Neon                                     |
| `FRONTEND_URL`      | yes      | Vercel origin, enables CORS                            |
| `BACKEND_BASE_URL`  | yes      | Public backend URL (for local-file URLs)               |
| `PORT`              | auto     | Injected by Render/Railway; default `8000` locally     |
| `GEMINI_API_KEY`    | optional | Enables Gemini AI feedback; blank = rule-based         |
| `CLOUDINARY_*`      | optional | Enables persistent cloud storage for uploads           |

### Frontend

| Variable       | Required | Notes                                              |
| -------------- | -------- | -------------------------------------------------- |
| `VITE_API_URL` | yes      | Absolute backend URL incl. `/api/v1` (build-time)  |
