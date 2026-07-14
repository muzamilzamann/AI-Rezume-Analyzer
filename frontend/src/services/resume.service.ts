import { api } from '@/lib/api'
import type {
  ParsedResume,
  ResumeRead,
  ResumeSummary,
  ResumeUploadResponse,
} from '@/types'

export const resumeService = {
  upload(file: File): Promise<ResumeUploadResponse> {
    const form = new FormData()
    form.append('file', file)
    return api
      .post<ResumeUploadResponse>('/resume/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })
      .then((res) => res.data)
  },
  list(): Promise<ResumeSummary[]> {
    return api.get<ResumeSummary[]>('/resume').then((res) => res.data)
  },
  get(id: string): Promise<ResumeRead> {
    return api.get<ResumeRead>(`/resume/${id}`).then((res) => res.data)
  },
  parsed(id: string): Promise<ParsedResume> {
    return api.get<ParsedResume>(`/resume/${id}/parsed`).then((res) => res.data)
  },
  remove(id: string): Promise<void> {
    return api.delete(`/resume/${id}`).then(() => undefined)
  },
}
