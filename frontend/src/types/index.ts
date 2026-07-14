export interface User {
  id: string
  name: string
  email: string
  is_active: boolean
  is_superuser: boolean
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface MessageResponse {
  message: string
}

export interface ApiErrorResponse {
  detail: string
}

export interface ParsedResume {
  name: string | null
  email: string | null
  phone: string | null
  skills: string[]
  education: string[]
  experience: string[]
  projects: string[]
  links: string[]
  word_count: number
}

export interface ResumeRead {
  id: string
  user_id: string
  file_url: string
  file_name: string
  content_type: string | null
  ats_score: number | null
  raw_text: string | null
  parsed_data: ParsedResume | null
  created_at: string
}

export interface ResumeSummary {
  id: string
  file_name: string
  ats_score: number | null
  created_at: string
  skills: string[]
}

export interface ResumeUploadResponse {
  resume: ResumeRead
  parsed: ParsedResume
}

export interface ATSSubscores {
  completeness: number
  formatting: number
  keywords: number
  length: number
  impact: number
}

export interface AnalysisRead {
  id: string
  resume_id: string
  overall_score: number | null
  subscores: Record<string, number> | null
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  source: string
  created_at: string
}

export interface AnalysisRunResponse {
  analysis: AnalysisRead
  resume_ats_score: number
}

export interface JobMatchRead {
  id: string
  resume_id: string
  job_title: string | null
  job_description: string
  match_score: number
  matching_skills: string[]
  missing_skills: string[]
  extra_skills: string[]
  recommendations: string[]
  created_at: string
}

export interface AdminStats {
  total_users: number
  active_users: number
  total_resumes: number
  total_analyses: number
  total_job_matches: number
  avg_ats_score: number | null
}

export interface AdminUserRead {
  id: string
  name: string
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  resume_count: number
}
