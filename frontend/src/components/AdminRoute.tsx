import { Navigate, Outlet } from 'react-router'
import { useAuth } from '@/hooks/useAuth'

export function AdminRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="text-sm text-slate-500">Loading…</span>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!user.is_superuser) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
