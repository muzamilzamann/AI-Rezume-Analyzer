import { api } from '@/lib/api'
import type { MessageResponse, Token, User } from '@/types'

export const authService = {
  register(data: { name: string; email: string; password: string }): Promise<User> {
    return api.post<User>('/auth/register', data).then((res) => res.data)
  },
  login(data: { email: string; password: string }): Promise<Token> {
    return api.post<Token>('/auth/login', data).then((res) => res.data)
  },
  me(): Promise<User> {
    return api.get<User>('/auth/me').then((res) => res.data)
  },
  forgotPassword(email: string): Promise<MessageResponse> {
    return api.post<MessageResponse>('/auth/forgot-password', { email }).then((res) => res.data)
  },
  resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
    return api
      .post<MessageResponse>('/auth/reset-password', { token, new_password: newPassword })
      .then((res) => res.data)
  },
}
