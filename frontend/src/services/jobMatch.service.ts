import { api } from '@/lib/api'
import type { JobMatchRead } from '@/types'

export interface JobMatchCreatePayload {
  resume_id: string
  job_title?: string | null
  job_description: string
}

export const jobMatchService = {
  create(payload: JobMatchCreatePayload): Promise<JobMatchRead> {
    return api.post<JobMatchRead>('/job-match', payload).then((res) => res.data)
  },
  list(resumeId: string): Promise<JobMatchRead[]> {
    return api.get<JobMatchRead[]>(`/job-match/${resumeId}`).then((res) => res.data)
  },
  get(matchId: string): Promise<JobMatchRead> {
    return api.get<JobMatchRead>(`/job-match/result/${matchId}`).then((res) => res.data)
  },
  remove(matchId: string): Promise<void> {
    return api.delete(`/job-match/result/${matchId}`).then(() => undefined)
  },
}
