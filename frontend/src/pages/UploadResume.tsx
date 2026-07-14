import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import toast from 'react-hot-toast'
import { CheckCircle2, FileText, UploadCloud, X } from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { Button } from '@/components/ui/Button'
import { getApiErrorMessage } from '@/lib/api'
import { resumeService } from '@/services/resume.service'
import type { ParsedResume } from '@/types'

const ACCEPTED = ['.pdf', '.docx']
const MAX_MB = 5

function acceptedFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return ACCEPTED.some((ext) => name.endsWith(ext))
}

export function UploadResume() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [parsed, setParsed] = useState<ParsedResume | null>(null)
  const [resumeId, setResumeId] = useState<string | null>(null)

  const handleFile = useCallback((next: File | null) => {
    setParsed(null)
    if (!next) {
      setFile(null)
      return
    }
    if (!acceptedFile(next)) {
      toast.error('Only PDF or DOCX files are supported.')
      return
    }
    if (next.size > MAX_MB * 1024 * 1024) {
      toast.error(`File too large. Maximum size is ${MAX_MB} MB.`)
      return
    }
    setFile(next)
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const next = e.dataTransfer.files?.[0]
      if (next) handleFile(next)
    },
    [handleFile],
  )

  const onUpload = async () => {
    if (!file) return
    setLoading(true)
    try {
      const result = await resumeService.upload(file)
      setParsed(result.parsed)
      setResumeId(result.resume.id)
      toast.success('Resume uploaded and parsed!')
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Upload failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            ← Back to dashboard
          </button>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">Upload your resume</h1>
          <p className="mt-1 text-sm text-slate-600">
            We&apos;ll extract your skills, experience, and education automatically. PDF or DOCX, up to {MAX_MB} MB.
          </p>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed bg-white px-6 py-12 text-center transition ${
            dragging ? 'border-brand-500 bg-brand-50' : 'border-slate-300 hover:border-brand-400'
          }`}
        >
          <UploadCloud className="h-10 w-10 text-brand-500" />
          <p className="mt-3 text-sm font-medium text-slate-900">
            Drag &amp; drop your resume here
          </p>
          <p className="mt-1 text-xs text-slate-500">or click to browse</p>
          <p className="mt-2 text-xs text-slate-400">Accepts {ACCEPTED.join(', ')}</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(',')}
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
        </div>

        {file && (
          <div className="mt-4 flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">{file.name}</p>
                <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {parsed && <CheckCircle2 className="h-5 w-5 text-green-500" />}
              <button
                onClick={() => handleFile(null)}
                className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                aria-label="Remove file"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={() => navigate('/dashboard')} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={onUpload} disabled={!file || loading} isLoading={loading}>
            {loading ? 'Uploading…' : 'Upload & parse'}
          </Button>
        </div>

        {parsed && (
          <ParsedPreview
            parsed={parsed}
            resumeId={resumeId}
            onView={(id) => navigate(`/resumes/${id}`)}
          />
        )}
      </main>
    </div>
  )
}

function ParsedPreview({
  parsed,
  resumeId,
  onView,
}: {
  parsed: ParsedResume
  resumeId: string | null
  onView: (id: string) => void
}) {
  return (
    <div className="mt-8 rounded-xl border border-green-200 bg-green-50 p-6">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-green-600" />
        <h2 className="text-base font-semibold text-green-900">Parsing complete</h2>
      </div>
      <p className="mt-1 text-sm text-green-800">
        We extracted {parsed.skills.length} skill{parsed.skills.length === 1 ? '' : 's'}
        {parsed.email ? ` · ${parsed.email}` : ''}.
      </p>

      {parsed.skills.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {parsed.skills.slice(0, 12).map((s) => (
            <span
              key={s}
              className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-green-800 ring-1 ring-inset ring-green-200"
            >
              {s}
            </span>
          ))}
          {parsed.skills.length > 12 && (
            <span className="px-2.5 py-1 text-xs text-green-700">+{parsed.skills.length - 12} more</span>
          )}
        </div>
      )}

      <div className="mt-5">
        <Button size="sm" disabled={!resumeId} onClick={() => resumeId && onView(resumeId)}>
          View full resume
        </Button>
      </div>
    </div>
  )
}
