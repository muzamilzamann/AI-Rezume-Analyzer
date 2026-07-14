import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  ExternalLink,
  GraduationCap,
  Lightbulb,
  Mail,
  Phone,
  Smartphone,
  Sparkles,
  Target,
  Trash2,
  User as UserIcon,
  Wrench,
} from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { Button } from '@/components/ui/Button'
import { getApiErrorMessage } from '@/lib/api'
import { analysisService } from '@/services/analysis.service'
import { resumeService } from '@/services/resume.service'
import type { AnalysisRead, ResumeRead } from '@/types'

export function ResumeDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [resume, setResume] = useState<ResumeRead | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisRead | null>(null)
  const [hasAnalysis, setHasAnalysis] = useState(false)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const loadAnalysis = useCallback(async (resumeId: string) => {
    try {
      const data = await analysisService.get(resumeId)
      setAnalysis(data)
      setHasAnalysis(true)
    } catch {
      setHasAnalysis(false)
    }
  }, [])

  useEffect(() => {
    if (!id) return
    resumeService
      .get(id)
      .then((r) => {
        setResume(r)
        return loadAnalysis(r.id)
      })
      .catch((err) => toast.error(getApiErrorMessage(err, 'Resume not found')))
      .finally(() => setLoading(false))
  }, [id, loadAnalysis])

  const handleAnalyze = async () => {
    if (!id) return
    setAnalyzing(true)
    try {
      const result = await analysisService.run(id)
      setAnalysis(result.analysis)
      setHasAnalysis(true)
      toast.success(`ATS score: ${result.resume_ats_score}/100`)
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Analysis failed'))
    } finally {
      setAnalyzing(false)
    }
  }

  const handleAIFeedback = async () => {
    if (!id) return
    setAiLoading(true)
    try {
      const result = await analysisService.runAIFeedback(id)
      setAnalysis(result.analysis)
      setHasAnalysis(true)
      const src = result.analysis.source
      toast.success(
        src === 'ai' ? 'AI suggestions generated!' : 'Suggestions generated (rule-based)',
      )
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'AI feedback failed'))
    } finally {
      setAiLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!id) return
    setDeleting(true)
    try {
      await resumeService.remove(id)
      toast.success('Resume deleted')
      navigate('/dashboard', { replace: true })
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Could not delete resume'))
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="mx-auto max-w-4xl px-4 py-16 text-center text-sm text-slate-500">
          Loading resume…
        </div>
      </div>
    )
  }

  if (!resume) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="mx-auto max-w-4xl px-4 py-16 text-center">
          <p className="text-sm text-slate-600">Resume not found.</p>
          <Link to="/dashboard" className="mt-3 inline-block text-sm font-medium text-brand-600">
            ← Back to dashboard
          </Link>
        </div>
      </div>
    )
  }

  const parsed = resume.parsed_data

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link to="/dashboard" className="text-sm font-medium text-slate-500 hover:text-slate-700">
              ← Back to dashboard
            </Link>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
              {parsed?.name || resume.file_name}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {resume.file_name} · uploaded {new Date(resume.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to={`/resumes/${resume.id}/match`}>
              <Button variant="secondary" size="sm">
                <Target className="h-4 w-4" />
                Match to job
              </Button>
            </Link>
            <Button variant="danger" size="sm" isLoading={deleting} onClick={handleDelete}>
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>

        <AnalysisPanel
          hasAnalysis={hasAnalysis}
          analysis={analysis}
          analyzing={analyzing}
          aiLoading={aiLoading}
          onAnalyze={handleAnalyze}
          onAIFeedback={handleAIFeedback}
        />

        {!parsed ? (
          <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
            This resume hasn&apos;t been parsed yet, or no text could be extracted.
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            <ContactCard parsed={parsed} />
            <SkillsCard skills={parsed.skills} />
            <SectionCard icon={<Briefcase className="h-5 w-5" />} title="Experience" items={parsed.experience} />
            <SectionCard icon={<GraduationCap className="h-5 w-5" />} title="Education" items={parsed.education} />
            <SectionCard icon={<Wrench className="h-5 w-5" />} title="Projects" items={parsed.projects} />
          </div>
        )}
      </main>
    </div>
  )
}

function AnalysisPanel({
  hasAnalysis,
  analysis,
  analyzing,
  aiLoading,
  onAnalyze,
  onAIFeedback,
}: {
  hasAnalysis: boolean
  analysis: AnalysisRead | null
  analyzing: boolean
  aiLoading: boolean
  onAnalyze: () => void
  onAIFeedback: () => void
}) {
  if (!hasAnalysis || !analysis) {
    return (
      <div className="flex flex-col items-center rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <Lightbulb className="h-6 w-6" />
        </div>
        <h2 className="mt-3 text-base font-semibold text-slate-900">Run an ATS analysis</h2>
        <p className="mt-1 max-w-sm text-sm text-slate-600">
          Score your resume on formatting, keyword coverage, completeness, length, and impact.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-3">
          <Button onClick={onAnalyze} isLoading={analyzing}>
            {analyzing ? 'Analyzing…' : 'Run ATS analysis'}
          </Button>
          <Button variant="secondary" onClick={onAIFeedback} isLoading={aiLoading}>
            <Sparkles className="h-4 w-4" />
            {aiLoading ? 'Generating…' : 'Get AI suggestions'}
          </Button>
        </div>
      </div>
    )
  }

  const score = analysis.overall_score ?? 0
  const subs = analysis.subscores ?? {}

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <ScoreGauge score={score} />
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              ATS Score
            </h2>
            <p className="text-2xl font-bold text-slate-900">{score.toFixed(1)}/100</p>
            <p className="text-xs text-slate-500">
              Feedback: {analysis.source === 'ai' ? 'AI (Gemini)' : analysis.source}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={onAnalyze} isLoading={analyzing}>
            Re-run ATS
          </Button>
          <Button size="sm" onClick={onAIFeedback} isLoading={aiLoading}>
            <Sparkles className="h-4 w-4" />
            {aiLoading ? 'Generating…' : 'AI suggestions'}
          </Button>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {(
          [
            ["completeness", "Completeness"],
            ["formatting", "Formatting"],
            ["keywords", "Keyword coverage"],
            ["length", "Length"],
            ["impact", "Impact"],
          ] as const
        ).map(([key, label]) => (
          <SubscoreBar key={key} label={label} value={subs[key] ?? 0} />
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <FeedbackList
          title="Strengths"
          icon={<CheckCircle2 className="h-4 w-4 text-green-500" />}
          items={analysis.strengths}
          emptyText="No standout strengths yet."
          tone="green"
        />
        <FeedbackList
          title="Weaknesses"
          icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}
          items={analysis.weaknesses}
          emptyText="No major weaknesses detected."
          tone="amber"
        />
        <FeedbackList
          title="Recommendations"
          icon={<Lightbulb className="h-4 w-4 text-brand-500" />}
          items={analysis.recommendations}
          emptyText="No recommendations."
          tone="brand"
        />
      </div>
    </div>
  )
}

function ScoreGauge({ score }: { score: number }) {
  const color =
    score >= 80 ? "#16a34a" : score >= 60 ? "#d97706" : "#dc2626"
  const circumference = 2 * Math.PI * 28
  const offset = circumference - (score / 100) * circumference
  return (
    <div className="relative h-20 w-20">
      <svg className="h-20 w-20 -rotate-90" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="none" stroke="#e2e8f0" strokeWidth="6" />
        <circle
          cx="32"
          cy="32"
          r="28"
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-slate-900">
        {Math.round(score)}
      </span>
    </div>
  )
}

function SubscoreBar({ label, value }: { label: string; value: number }) {
  const color =
    value >= 80 ? "bg-green-500" : value >= 60 ? "bg-amber-500" : "bg-red-500"
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-900">{Math.round(value)}/100</span>
      </div>
      <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

function FeedbackList({
  title,
  icon,
  items,
  emptyText,
  tone,
}: {
  title: string
  icon: React.ReactNode
  items: string[]
  emptyText: string
  tone: "green" | "amber" | "brand"
}) {
  const badge =
    tone === "green"
      ? "bg-green-50 text-green-700"
      : tone === "amber"
        ? "bg-amber-50 text-amber-700"
        : "bg-brand-50 text-brand-700"
  return (
    <div className={`rounded-lg p-4 ${badge}`}>
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      {items.length === 0 ? (
        <p className="mt-2 text-xs opacity-70">{emptyText}</p>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {items.map((item, i) => (
            <li key={i} className="text-xs leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ContactCard({ parsed }: { parsed: NonNullable<ResumeRead['parsed_data']> }) {
  const rows = [
    parsed.name ? { icon: <UserIcon className="h-4 w-4" />, label: parsed.name } : null,
    parsed.email ? { icon: <Mail className="h-4 w-4" />, label: parsed.email } : null,
    parsed.phone ? { icon: <Phone className="h-4 w-4" />, label: parsed.phone } : null,
    parsed.links.length > 0
      ? { icon: <ExternalLink className="h-4 w-4" />, label: parsed.links.join(' · ') }
      : null,
  ].filter(Boolean)

  if (rows.length === 0) return null

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Contact</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {rows.map((row, i) => (
          <div key={i} className="flex items-center gap-2 text-sm text-slate-700">
            <span className="text-brand-600">{row!.icon}</span>
            <span className="truncate">{row!.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function SkillsCard({ skills }: { skills: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Skills</h2>
        <span className="flex items-center gap-1 text-xs text-slate-400">
          <Smartphone className="h-3.5 w-3.5" /> {skills.length} found
        </span>
      </div>
      {skills.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No skills detected.</p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {skills.map((s) => (
            <span
              key={s}
              className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700 ring-1 ring-inset ring-brand-200"
            >
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function SectionCard({
  icon,
  title,
  items,
}: {
  icon: React.ReactNode
  title: string
  items: string[]
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-brand-600">{icon}</span>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h2>
      </div>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">Nothing detected.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((item, i) => (
            <li key={i} className="text-sm leading-relaxed text-slate-700">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
