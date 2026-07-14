import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import toast from 'react-hot-toast'
import { CheckCircle2, Lightbulb, Target, XCircle } from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { Button } from '@/components/ui/Button'
import { getApiErrorMessage } from '@/lib/api'
import { jobMatchService } from '@/services/jobMatch.service'
import type { JobMatchRead } from '@/types'

export function JobMatch() {
  const { id } = useParams<{ id: string }>()
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [matches, setMatches] = useState<JobMatchRead[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!id) return
    jobMatchService
      .list(id)
      .then(setMatches)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  const handleMatch = async () => {
    if (!id) return
    if (jobDescription.trim().length < 10) {
      toast.error('Please paste a job description (at least 10 characters).')
      return
    }
    setSubmitting(true)
    try {
      const match = await jobMatchService.create({
        resume_id: id,
        job_title: jobTitle.trim() || null,
        job_description: jobDescription.trim(),
      })
      setMatches((prev) => [match, ...prev])
      toast.success(`Match score: ${match.match_score}%`)
      setJobDescription('')
      setJobTitle('')
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Matching failed'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (matchId: string) => {
    try {
      await jobMatchService.remove(matchId)
      setMatches((prev) => prev.filter((m) => m.id !== matchId))
      toast.success('Match deleted')
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Could not delete match'))
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <Link
            to={id ? `/resumes/${id}` : '/dashboard'}
            className="text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            ← Back to resume
          </Link>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">Job matching</h1>
          <p className="mt-1 text-sm text-slate-600">
            Paste a job description to see how well your resume matches and which skills are missing.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Job title (optional)
              </label>
              <input
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Senior Backend Engineer"
                className="block w-full rounded-lg border-0 bg-white px-3.5 py-2.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Job description
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={8}
                placeholder="Paste the full job description here…"
                className="block w-full rounded-lg border-0 bg-white px-3.5 py-2.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm"
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleMatch} isLoading={submitting} disabled={!jobDescription.trim()}>
                <Target className="h-4 w-4" />
                Calculate match
              </Button>
            </div>
          </div>
        </div>

        <div className="mt-8 space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">
            {loading ? 'Loading matches…' : `Match history (${matches.length})`}
          </h2>
          {matches.map((m) => (
            <MatchCard key={m.id} match={m} onDelete={() => handleDelete(m.id)} />
          ))}
          {!loading && matches.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
              No matches yet. Paste a job description above to get started.
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function MatchCard({ match, onDelete }: { match: JobMatchRead; onDelete: () => void }) {
  const score = match.match_score
  const color =
    score >= 80 ? 'text-green-600' : score >= 50 ? 'text-amber-600' : 'text-red-600'
  const ring =
    score >= 80 ? 'ring-green-200 bg-green-50' : score >= 50 ? 'ring-amber-200 bg-amber-50' : 'ring-red-200 bg-red-50'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            {match.job_title || 'Untitled role'}
          </h3>
          <p className="text-xs text-slate-500">
            {new Date(match.created_at).toLocaleString()}
          </p>
        </div>
        <div className={`flex items-center gap-2 rounded-full px-3 py-1 ring-1 ring-inset ${ring}`}>
          <Target className={`h-4 w-4 ${color}`} />
          <span className={`text-sm font-bold ${color}`}>{score}% match</span>
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <SkillGroup
          title="Matching skills"
          icon={<CheckCircle2 className="h-4 w-4 text-green-500" />}
          skills={match.matching_skills}
          tone="green"
        />
        <SkillGroup
          title="Missing skills"
          icon={<XCircle className="h-4 w-4 text-red-500" />}
          skills={match.missing_skills}
          tone="red"
        />
      </div>

      {match.recommendations.length > 0 && (
        <div className="mt-4 rounded-lg bg-brand-50 p-4">
          <div className="flex items-center gap-2 text-brand-700">
            <Lightbulb className="h-4 w-4" />
            <h4 className="text-sm font-semibold">Recommendations</h4>
          </div>
          <ul className="mt-2 space-y-1">
            {match.recommendations.map((r, i) => (
              <li key={i} className="text-xs text-brand-800">{r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex justify-end">
        <Button variant="ghost" size="sm" onClick={onDelete}>
          Delete
        </Button>
      </div>
    </div>
  )
}

function SkillGroup({
  title,
  icon,
  skills,
  tone,
}: {
  title: string
  icon: React.ReactNode
  skills: string[]
  tone: 'green' | 'red'
}) {
  const chip =
    tone === 'green'
      ? 'bg-green-50 text-green-700 ring-green-200'
      : 'bg-red-50 text-red-700 ring-red-200'
  return (
    <div>
      <div className="flex items-center gap-2">
        {icon}
        <h4 className="text-sm font-medium text-slate-700">{title}</h4>
        <span className="text-xs text-slate-400">({skills.length})</span>
      </div>
      {skills.length === 0 ? (
        <p className="mt-2 text-xs text-slate-400">None</p>
      ) : (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {skills.map((s) => (
            <span
              key={s}
              className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${chip}`}
            >
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
