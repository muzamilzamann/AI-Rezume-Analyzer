import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { clearToken, getToken, setToken } from '@/lib/api'
import { authService } from '@/services/auth.service'
import { AuthContext } from './auth-context'
import type { User } from '@/types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    authService
      .me()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authService.login({ email, password })
    setToken(access_token)
    const me = await authService.me()
    setUser(me)
  }, [])

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      await authService.register({ name, email, password })
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
