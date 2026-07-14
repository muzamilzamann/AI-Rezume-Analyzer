"""Resume text extraction and heuristic parsing.

PDF text is extracted with ``pdfplumber`` and DOCX with ``python-docx`` (both
imported lazily so the heavy parsing deps are only required at runtime). The
structured extraction is intentionally lightweight (regex + section headers) so
it works without an NLP model; spaCy/Gemini enhancements arrive in later weeks.
"""

from __future__ import annotations

import re

from app.schemas.resume import ParsedResume


# --------------------------------------------------------------------------- #
# Text extraction
# --------------------------------------------------------------------------- #
def _extract_pdf(data: bytes) -> str:
    import io

    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def _extract_docx(data: bytes) -> str:
    import io

    from docx import Document

    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def extract_text(data: bytes, content_type: str | None, filename: str) -> str:
    """Extract plain text from a PDF or DOCX blob. Returns '' if unsupported."""
    name = (filename or "").lower()
    ct = (content_type or "").lower()

    if ct == "application/pdf" or name.endswith(".pdf"):
        return _extract_pdf(data)
    if (
        ct == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or name.endswith(".docx")
    ):
        return _extract_docx(data)
    if name.endswith(".doc"):
        # Legacy .doc is not supported by python-docx; surface empty text.
        return ""
    return ""


# --------------------------------------------------------------------------- #
# Skill catalogue (canonical -> lowercase matcher)
# --------------------------------------------------------------------------- #
_SKILL_CATALOGUE = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go", "Golang",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Dart",
    "SQL", "Bash", "Shell", "Perl", "Objective-C", "HTML", "CSS", "Solidity",
    # Frontend
    "React", "React.js", "Next.js", "Vue", "Vue.js", "Angular", "Svelte",
    "Redux", "Tailwind CSS", "TailwindCSS", "Sass", "SCSS", "Bootstrap",
    "Material UI", "Chakra UI", "Vite", "Webpack",
    # Backend
    "FastAPI", "Flask", "Django", "Express", "Express.js", "NestJS", "Spring",
    "Spring Boot", "Node.js", "NodeJS", "Rails", "Ruby on Rails", "ASP.NET",
    ".NET", "GraphQL", "REST", "gRPC", "WebSocket", "Microservices",
    # Mobile / Desktop
    "React Native", "Flutter", "Android", "iOS", "Electron", "Qt",
    # Data / ML
    "Pandas", "NumPy", "SciPy", "scikit-learn", "TensorFlow", "PyTorch",
    "Keras", "XGBoost", "NLTK", "spaCy", "OpenCV", "Hugging Face", "LangChain",
    "Matplotlib", "Seaborn", "Plotly", "Spark", "Apache Spark", "Hadoop", "Kafka",
    "Airflow", "dbt", "Power BI", "Tableau", "Looker",
    # Databases
    "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
    "DynamoDB", "Elasticsearch", "Cassandra", "Firebase", "Supabase", "Prisma",
    "SQLAlchemy", "Sequelize", "TypeORM",
    # Cloud / DevOps
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform",
    "Ansible", "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Helm",
    "Nginx", "Linux", "Unix", "Bash", "Prometheus", "Grafana", "Cloudflare",
    "Serverless", "Lambda",
    # Tools / Practices
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Agile", "Scrum", "Kanban",
    "CI/CD", "TDD", "OOP", "System Design", "REST API", "OAuth", "JWT",
    "WebSocket", "RabbitMQ", "Celery",
]

# Map a normalized matcher to its canonical display name.
_SKILL_MATCHERS: dict[str, str] = {}
for _skill in _SKILL_CATALOGUE:
    _key = re.sub(r"[.\s+#]", "", _skill).lower()
    # Prefer the first canonical spelling for collisions (e.g. Node.js / NodeJS).
    _SKILL_MATCHERS.setdefault(_key, _skill)


# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(\+?\d[\d\s().\-]{8,}\d)"
)
_URL_RE = re.compile(
    r"(https?://[^\s)]+|(?:www\.)?[a-z0-9.\-]+\.(?:com|io|dev|net|org|me|ai|co)(?:/[^\s)]*)?)",
    re.IGNORECASE,
)
_LINKEDIN_RE = re.compile(r"(linkedin\.com/[^\s)]+)", re.IGNORECASE)
_GITHUB_RE = re.compile(r"(github\.com/[^\s)]+)", re.IGNORECASE)

# Section header keywords mapped to a canonical section.
_SECTION_MAP = {
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "work history": "experience",
    "education": "education",
    "academic": "education",
    "projects": "projects",
    "personal projects": "projects",
    "side projects": "projects",
    "technical projects": "projects",
    "skills": "skills",
    "technical skills": "skills",
    "core competencies": "skills",
    "technologies": "skills",
}


def _guess_name(lines: list[str]) -> str | None:
    for raw in lines[:8]:
        line = raw.strip()
        if not line:
            continue
        if _EMAIL_RE.search(line) or _PHONE_RE.search(line) or _URL_RE.search(line):
            continue
        # Skip pure section headers / all-caps labels.
        if line.lower().rstrip(":") in _SECTION_MAP:
            continue
        words = line.split()
        if 1 < len(words) <= 5 and re.match(r"^[A-Za-z][A-Za-z .'\-]+$", line):
            return " ".join(w.capitalize() for w in words)
    return None


def _split_sections(text: str) -> dict[str, list[str]]:
    """Group lines under recognized section headers. Unmatched lines go to '_'."""
    sections: dict[str, list[str]] = {"_": []}
    current = "_"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        key = line.lower().rstrip(":").strip()
        if key in _SECTION_MAP and len(line.split()) <= 4:
            current = _SECTION_MAP[key]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _entries(lines: list[str]) -> list[str]:
    """Collapse a section's lines into discrete entries (by blank-line / bullet)."""
    if not lines:
        return []
    joined = "\n".join(lines)
    # Split on bullet markers or newlines that look like new entries.
    parts = re.split(r"(?:\n|•|·|\*|-)\s*(?=[A-Z0-9])", joined)
    cleaned: list[str] = []
    seen: set[str] = set()
    for part in parts:
        item = " ".join(part.split()).strip(" -*•·")
        if item and item not in seen and len(item) > 2:
            seen.add(item)
            cleaned.append(item)
    return cleaned


def _detect_skills(text: str) -> list[str]:
    haystack = re.sub(r"[.\s+#]", "", text).lower()
    found: list[str] = []
    seen: set[str] = set()
    for matcher, canonical in _SKILL_MATCHERS.items():
        if matcher in haystack and canonical.lower() not in seen:
            # Avoid short matcher false positives (e.g. "c", "r", "go").
            if len(matcher) <= 2 and not re.search(
                rf"(?<![a-z0-9]){re.escape(matcher)}(?![a-z0-9])", haystack
            ):
                continue
            seen.add(canonical.lower())
            found.append(canonical)
    return found


def detect_skills(text: str) -> list[str]:
    """Public wrapper around the internal skill detector (used by job matching)."""
    return _detect_skills(text)


def parse_resume(text: str) -> ParsedResume:
    raw = text or ""
    compact = re.sub(r"[ \t]+", " ", raw)
    lines = [ln.strip() for ln in compact.splitlines()]

    email_match = _EMAIL_RE.search(raw)
    phone_match = _PHONE_RE.search(raw)
    links: list[str] = []
    for m in _LINKEDIN_RE.findall(raw) + _GITHUB_RE.findall(raw):
        link = m.strip().rstrip(".,);")
        if link not in links:
            links.append(link)
    for m in _URL_RE.findall(raw):
        link = m.strip().rstrip(".,);")
        if link.lower().startswith(("http", "www.")) and link not in links:
            links.append(link)

    skills = _detect_skills(raw)
    sections = _split_sections(compact)
    experience = _entries(sections.get("experience", []))
    education = _entries(sections.get("education", []))
    projects = _entries(sections.get("projects", []))

    name = _guess_name(lines)

    return ParsedResume(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(1).strip() if phone_match else None,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        links=links,
        word_count=len(raw.split()),
    )
