import { api } from '@/lib/api'
import type { AnalysisRead, AnalysisRunResponse } from '@/types'

export const analysisService = {
  run(resumeId: string): Promise<AnalysisRunResponse> {
    return api
      .post<AnalysisRunResponse>('/analysis/run', { resume_id: resumeId }, { timeout: 60000 })
      .then((res) => res.data)
  },
  runAIFeedback(resumeId: string): Promise<AnalysisRunResponse> {
    return api
      .post<AnalysisRunResponse>(
        '/analysis/ai-feedback',
        { resume_id: resumeId },
        { timeout: 90000 },
      )
      .then((res) => res.data)
  },
  get(resumeId: string): Promise<AnalysisRead> {
    return api.get<AnalysisRead>(`/analysis/${resumeId}`).then((res) => res.data)
  },
}
