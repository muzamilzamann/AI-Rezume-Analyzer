# Development Plan & Architecture

## 8-Week Roadmap

| Week | Focus                                            | Status |
| ---- | ------------------------------------------------ | ------ |
| 1    | Project setup, database, authentication          | ✅ Done |
| 2    | Resume upload (Cloudinary) and parsing           | ✅ Done |
| 3    | ATS scoring system                               | ⏳     |
| 4    | AI feedback generation (Gemini)                  | ⏳     |
| 5    | Job description matching                         | ⏳     |
| 6    | Dashboard and admin panel                        | ⏳     |
| 7    | Docker, testing, and CI/CD                       | ⏳     |
| 8    | Deploy frontend, backend, and database           | ⏳     |

---

## Data Model

```
users
├── id            UUID PK
├── name          VARCHAR(100)
├── email         VARCHAR(255) UNIQUE
├── password_hash VARCHAR(255)
├── is_active     BOOLEAN
├── is_superuser  BOOLEAN
└── created_at    TIMESTAMPTZ

resumes
├── id          UUID PK
├── user_id     UUID FK -> users.id (CASCADE)
├── file_url    VARCHAR(1024)
├── file_name   VARCHAR(255)
├── storage_id  VARCHAR(512) (nullable)   # Cloudinary public_id / local filename
├── content_type VARCHAR(100) (nullable)
├── ats_score   FLOAT (nullable)
├── raw_text    TEXT (nullable)           # extracted plain text
├── parsed_data JSONB (nullable)          # {name, email, phone, skills, ...}
└── created_at  TIMESTAMPTZ

analyses
├── id              UUID PK
├── resume_id       UUID FK -> resumes.id (CASCADE, UNIQUE)
├── strengths       JSONB
├── weaknesses      JSONB
├── recommendations JSONB
└── created_at      TIMESTAMPTZ
```

Relationships: a `user` has many `resumes`; a `resume` has one `analysis`.

---

## API Surface (target)

| Method | Endpoint                  | Description                       |
| ------ | ------------------------- | --------------------------------- |
| `POST` | `/api/v1/auth/register`   | Create account                    |
| `POST` | `/api/v1/auth/login`      | Login, returns JWT                |
| `GET`  | `/api/v1/auth/me`         | Current user                      |
| `POST` | `/api/v1/resume/upload`   | Upload resume (PDF/DOCX) + parse  |
| `GET`  | `/api/v1/resume`          | List current user's resumes       |
| `GET`  | `/api/v1/resume/{id}`     | Fetch a resume + parsed data      |
| `GET`  | `/api/v1/resume/{id}/parsed` | Fetch structured parse only    |
| `DELETE` | `/api/v1/resume/{id}`   | Delete a resume + its file        |
| `POST` | `/api/v1/analysis/run`    | Run ATS + AI analysis (Week 3+)   |
| `POST` | `/api/v1/job-match`       | Match resume vs. job description (Week 5+) |

---

## Architecture Notes

- **Backend**: layered — `api/` (transport) → `services/` (business logic) → `models/` (persistence). Async SQLAlchemy 2.0 with asyncpg; Alembic for migrations.
- **Auth**: stateless JWT (HS256). Passwords hashed with bcrypt. Token in `Authorization: Bearer <token>`.
- **Frontend**: feature-oriented folders; axios client with token interceptor; React Context for auth state; React Router with a protected-route guard.
- **Config**: all secrets via environment variables (`pydantic-settings`); `.env` files are git-ignored.
- **Storage**: files are uploaded to Cloudinary when `CLOUDINARY_*` env vars are set; otherwise the service transparently falls back to the local filesystem (served via the mounted `/uploads` static route). This keeps the upload flow fully functional in local dev without a Cloudinary account.
- **Parsing**: PDF text via `pdfplumber`, DOCX via `python-docx` (both lazy-imported). Structured extraction is heuristic (regex + section headers) — email/phone/links, a curated skill catalogue, and experience/education/projects sections. The raw text and structured `parsed_data` are persisted on the resume row for later ATS/AI features.
