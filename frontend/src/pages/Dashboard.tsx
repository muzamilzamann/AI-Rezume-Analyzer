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
    status: 'Coming soon',
    accent: 'bg-amber-50 text-amber-600',
  },
  {
    icon: BarChart3,
    title: 'ATS Score',
    description: 'Formatting, keyword, and skills scoring.',
    status: 'Coming soon',
    accent: 'bg-amber-50 text-amber-600',
  },
  {
    icon: Sparkles,
    title: 'AI Suggestions',
    description: 'Recruiter-grade improvement recommendations.',
    status: 'Coming soon',
    accent: 'bg-amber-50 text-amber-600',
  },
  {
    icon: Target,
    title: 'Job Matching',
    description: 'Compare your resume against a job description.',
    status: 'Coming soon',
    accent: 'bg-amber-50 text-amber-600',
  },
]

export function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Welcome back, {user?.name?.split(' ')[0] ?? 'there'} 👋
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Here's an overview of your resume analysis activity.
          </p>
        </div>

        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          {[
            { label: 'Resumes uploaded', value: '0' },
            { label: 'Average ATS score', value: '—' },
            { label: 'Jobs matched', value: '0' },
          ].map((stat) => (
            <div key={stat.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">{stat.label}</p>
              <p className="mt-1 text-3xl font-bold text-slate-900">{stat.value}</p>
            </div>
          ))}
        </div>

        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Quick actions</h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map(({ icon: Icon, title, description, status, accent }) => (
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
              <Link to="/dashboard" className="mt-4">
                <Button variant="secondary" size="sm" className="w-full" disabled={status !== 'Ready'}>
                  {status === 'Ready' ? 'Upload resume' : 'Not available yet'}
                </Button>
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-8 flex items-start gap-3 rounded-xl border border-brand-100 bg-brand-50 p-5">
          <FileText className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
          <div>
            <p className="text-sm font-medium text-brand-900">You're all set for Week 1</p>
            <p className="mt-1 text-sm text-brand-700">
              Authentication is live. Resume upload, parsing, and ATS scoring arrive in the
              upcoming weeks.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
