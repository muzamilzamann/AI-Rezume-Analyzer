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
