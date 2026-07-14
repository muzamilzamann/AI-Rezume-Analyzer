import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import {
  BarChart3,
  FileSearch,
  FileText,
  Sparkles,
  Target,
  Upload,
} from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { resumeService } from '@/services/resume.service'
import type { ResumeSummary } from '@/types'

const cards = [
  {
    icon: Upload,
    title: 'Upload Resume',
    description: 'Upload a PDF or DOCX resume to get started.',
    status: 'Ready',
    accent: 'bg-brand-50 text-brand-600',
  },
  {
    icon: FileSearch,
    title: 'Resume Parsing',
    description: 'Auto-extract skills, experience, and education.',
    status: 'Ready',
    accent: 'bg-brand-50 text-brand-600',
  },
  {
    icon: BarChart3,
    title: 'ATS Score',
    description: 'Formatting, keyword, and skills scoring.',
    status: 'Ready',
    accent: 'bg-brand-50 text-brand-600',
  },
  {
    icon: Sparkles,
    title: 'AI Suggestions',
    description: 'Recruiter-grade improvement recommendations.',
    status: 'Ready',
    accent: 'bg-brand-50 text-brand-600',
  },
  {
    icon: Target,
    title: 'Job Matching',
    description: 'Compare your resume against a job description.',
    status: 'Ready',
    accent: 'bg-brand-50 text-brand-600',
  },
]

export function Dashboard() {
  const { user } = useAuth()
  const [resumes, setResumes] = useState<ResumeSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    resumeService
      .list()
      .then(setResumes)
      .finally(() => setLoading(false))
  }, [])

  const scored = resumes.filter((r) => r.ats_score != null)
  const avgAts =
    scored.length > 0
      ? (scored.reduce((sum, r) => sum + (r.ats_score ?? 0), 0) / scored.length).toFixed(1)
      : null
  const totalSkills = new Set(resumes.flatMap((r) => r.skills)).size

  const stats = [
    { label: 'Resumes uploaded', value: String(resumes.length) },
    { label: 'Average ATS score', value: avgAts ? `${avgAts}/100` : '—' },
    { label: 'Unique skills tracked', value: String(totalSkills) },
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Welcome back, {user?.name?.split(' ')[0] ?? 'there'} 👋
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Here&apos;s an overview of your resume analysis activity.
            </p>
          </div>
          <Link to="/dashboard/upload">
            <Button>
              <Upload className="h-4 w-4" />
              Upload resume
            </Button>
          </Link>
        </div>

        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <p className="text-sm text-slate-500">{stat.label}</p>
              <p className="mt-1 text-3xl font-bold text-slate-900">
                {loading ? '…' : stat.value}
              </p>
            </div>
          ))}
        </div>

        <RecentResumes resumes={resumes} loading={loading} />

        <div className="mb-6 mt-10 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Quick actions</h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map(({ icon: Icon, title, description, status, accent }) => {
            const target =
              title === 'Upload Resume' || resumes.length === 0
                ? '/dashboard/upload'
                : `/resumes/${resumes[0].id}`
            return (
              <div
                key={title}
                className="flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${accent}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                    {status}
                  </span>
                </div>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
                <p className="mt-1 flex-1 text-sm text-slate-600">{description}</p>
                <Link to={target} className="mt-4">
                  <Button variant="secondary" size="sm" className="w-full">
                    {title === 'Upload Resume' ? 'Upload resume' : 'Open'}
                  </Button>
                </Link>
              </div>
            )
          })}
        </div>

        <div className="mt-8 flex items-start gap-3 rounded-xl border border-brand-100 bg-brand-50 p-5">
          <FileText className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
          <div>
            <p className="text-sm font-medium text-brand-900">All core features are live</p>
            <p className="mt-1 text-sm text-brand-700">
              Upload a resume, run ATS scoring, get AI suggestions, and match against job
              descriptions. An admin panel is available to superusers.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

function RecentResumes({
  resumes,
  loading,
}: {
  resumes: ResumeSummary[]
  loading: boolean
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">Recent resumes</h2>
        <Link
          to="/dashboard/upload"
          className="text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          Upload new
        </Link>
      </div>

      {loading ? (
        <div className="px-5 py-8 text-center text-sm text-slate-500">Loading…</div>
      ) : resumes.length === 0 ? (
        <div className="flex flex-col items-center px-5 py-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
            <Upload className="h-6 w-6" />
          </div>
          <p className="mt-3 text-sm font-medium text-slate-900">No resumes yet</p>
          <p className="mt-1 text-sm text-slate-500">
            Upload your first resume to see it parsed here.
          </p>
          <Link to="/dashboard/upload" className="mt-4">
            <Button size="sm">
              <Upload className="h-4 w-4" />
              Upload resume
            </Button>
          </Link>
        </div>
      ) : (
        <ul className="divide-y divide-slate-100">
          {resumes.map((r) => (
            <li key={r.id}>
              <Link
                to={`/resumes/${r.id}`}
                className="flex items-center justify-between px-5 py-4 transition hover:bg-slate-50"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{r.file_name}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(r.created_at).toLocaleDateString()}
                      {r.skills.length > 0 && ` · ${r.skills.length} skills`}
                    </p>
                  </div>
                </div>
                {r.ats_score != null && (
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                    ATS {Math.round(r.ats_score)}
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
