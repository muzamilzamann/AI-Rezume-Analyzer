import { Link } from 'react-router'
import { BarChart3, FileSearch, Sparkles, Target } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'

const features = [
  {
    icon: FileSearch,
    title: 'Smart Resume Parsing',
    description: 'Extract skills, experience, and education from PDF/DOCX in seconds.',
  },
  {
    icon: BarChart3,
    title: 'ATS Score Analysis',
    description: 'See how your resume scores on formatting, keywords, and skills.',
  },
  {
    icon: Sparkles,
    title: 'AI-Powered Suggestions',
    description: 'Get actionable, recruiter-grade feedback powered by Gemini.',
  },
  {
    icon: Target,
    title: 'Job Match Scoring',
    description: 'Compare your resume to any job description and close the gaps.',
  },
]

export function Landing() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white">
      <header className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white font-bold">
            R
          </div>
          <span className="text-lg font-semibold text-slate-900">Resume Analyzer</span>
        </div>
        <div className="flex gap-2">
          {user ? (
            <Button size="sm" onClick={() => (window.location.href = '/dashboard')}>
              Go to Dashboard
            </Button>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => (window.location.href = '/login')}>
                Log in
              </Button>
              <Button size="sm" onClick={() => (window.location.href = '/register')}>
                Get started
              </Button>
            </>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 sm:px-6">
        <section className="py-20 text-center sm:py-28">
          <span className="inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-sm font-medium text-brand-700">
            <Sparkles className="h-4 w-4" /> AI-powered resume optimization
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
            Land more interviews with a recruiter-ready resume
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
            Upload your resume and get instant ATS scoring, AI-driven suggestions, and a
            side-by-side match against any job description.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link to="/register">
              <Button size="lg">Start analyzing — free</Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg">
                I already have an account
              </Button>
            </Link>
          </div>
        </section>

        <section className="grid gap-6 pb-24 sm:grid-cols-2 lg:grid-cols-4">
          {features.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 text-sm text-slate-600">{description}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  )
}
