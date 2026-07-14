# AI Resume Analyzer

An AI-powered resume analysis platform that parses resumes, scores them against
Applicant Tracking Systems (ATS), generates recruiter-grade improvement
suggestions, and matches candidates against job descriptions.

Built as a production-ready portfolio project demonstrating a modern AI full-stack
architecture: **React + TypeScript** frontend, **FastAPI + async SQLAlchemy**
backend, **PostgreSQL** (Neon), and **Google Gemini** for AI features.

---

## ✨ Features

- **Authentication** — signup/login, JWT auth, password reset flow.
- **Dashboard** — manage resumes, view past analyses, download reports.
- **Resume Parser** — extract name, email, skills, education, experience, projects from PDF/DOCX.
- **ATS Scoring** — formatting, keywords, and skills subscores with an overall score.
- **AI Suggestions** — actionable feedback powered by Google Gemini.
- **Job Matching** — compare a resume to a job description; see match %, missing skills, and recommendations.
- **Admin Panel** — user management and analytics (planned).

> **Status:** Week 1 complete — project scaffold, database, and JWT authentication are live. Resume parsing, ATS scoring, AI feedback, job matching, and deployment arrive in the following weeks (see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)).

---

## 🧱 Tech Stack

| Layer      | Technology                                              |
| ---------- | ------------------------------------------------------- |
| Frontend   | React 19, TypeScript, Tailwind CSS v4, React Router v8  |
| Backend    | Python, FastAPI, async SQLAlchemy 2.0, Pydantic v2      |
| Database   | PostgreSQL (Neon serverless)                            |
| AI         | Google Gemini API, spaCy, pdfplumber                    |
| Storage    | Cloudinary                                              |
| Dev tooling| uv, Vite, Alembic, ruff, oxlint, pytest                 |
| Deployment | Docker, GitHub Actions (CI/CD), Vercel, Railway/Render  |

---

## 📁 Project Structure

```
resume-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Route handlers (auth, ...)
│   │   ├── core/               # config, database, security
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   ├── utils/
│   │   └── main.py             # FastAPI app entrypoint
│   ├── alembic/                # Database migrations
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/         # UI + layout components
│   │   ├── context/            # React context providers
│   │   ├── hooks/              # Custom hooks
│   │   ├── lib/                # API client & utilities
│   │   ├── pages/              # Route pages
│   │   ├── services/           # API service modules
│   │   └── types/              # TypeScript types
│   └── .env.example
├── docker/
├── docs/
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.12+](https://www.python.org/) (managed automatically by [uv](https://docs.astral.sh/uv/))
- [Node.js 20+](https://nodejs.org/)
- A [Neon](https://neon.tech) PostgreSQL project (free tier)
- [uv](https://docs.astral.sh/uv/) installed globally

### 1. Clone & install

```bash
git clone <repo-url>
cd "AI Resume Analyzer"
```

### 2. Backend setup

```bash
cd backend
cp .env.example .env          # fill in DATABASE_URL and JWT_SECRET_KEY
uv sync --extra dev           # installs Python 3.12 + dependencies
uv run alembic upgrade head   # create database tables
uv run uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000` with interactive docs at
`http://localhost:8000/docs`.

### 3. Frontend setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The app runs at `http://localhost:5173` and proxies `/api` requests to the backend.

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable                  | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `DATABASE_URL`            | Neon connection string (auto-normalized for asyncpg)   |
| `DB_SSL_MODE`             | SSL mode for Postgres (`require` for Neon)             |
| `JWT_SECRET_KEY`          | Secret used to sign JWTs                               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 1440 = 1 day)       |
| `GEMINI_API_KEY`          | Google Gemini API key (Week 4+)                        |
| `CLOUDINARY_*`            | Cloudinary credentials (Week 2+)                       |

Generate a JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Frontend (`frontend/.env`)

| Variable       | Description                                   |
| -------------- | --------------------------------------------- |
| `VITE_API_URL` | API base URL (default `/api/v1` via dev proxy)|

---

## 🗄️ Database

This project uses [Neon](https://neon.tech) serverless PostgreSQL.

1. Create a free Neon project and copy the connection string.
2. Paste it into `backend/.env` as `DATABASE_URL`.
3. Run `uv run alembic upgrade head` to apply migrations.

The connection string is normalized at runtime: plain `postgresql://` URLs and
`sslmode=require` query params (as Neon provides them) are converted to the
asyncpg-compatible form automatically.

### Schema

- **users** — `id`, `name`, `email`, `password_hash`, `is_active`, `is_superuser`, `created_at`
- **resumes** — `id`, `user_id`, `file_url`, `file_name`, `ats_score`, `created_at`
- **analyses** — `id`, `resume_id`, `strengths`, `weaknesses`, `recommendations`, `created_at`

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the full data model.

---

## 📡 API Endpoints

| Method | Endpoint                  | Description                |
| ------ | ------------------------- | -------------------------- |
| `POST` | `/api/v1/auth/register`   | Create a new account       |
| `POST` | `/api/v1/auth/login`      | Authenticate & get JWT     |
| `GET`  | `/api/v1/auth/me`         | Get current user           |
| `POST` | `/api/v1/auth/forgot-password` | Request a reset token |
| `POST` | `/api/v1/auth/reset-password`  | Reset password        |
| `GET`  | `/health`                 | Service health check       |

Full interactive documentation is available at `/docs` when the backend is running.

---

## 🧪 Testing & Linting

```bash
# Backend
cd backend
uv run ruff check .
uv run pytest

# Frontend
cd frontend
npm run lint
npm run build
```

---

## 📅 Roadmap

An 8-week development plan is documented in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## 📄 License

MIT
