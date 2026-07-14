import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Activity, ShieldCheck, Users } from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { Button } from '@/components/ui/Button'
import { getApiErrorMessage } from '@/lib/api'
import { adminService } from '@/services/admin.service'
import type { AdminStats, AdminUserRead } from '@/types'

export function Admin() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [users, setUsers] = useState<AdminUserRead[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const [s, u] = await Promise.all([adminService.stats(), adminService.users()])
      setStats(s)
      setUsers(u)
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Failed to load admin data'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const toggleActive = async (user: AdminUserRead) => {
    const next = !user.is_active
    try {
      const updated = await adminService.setUserActive(user.id, next)
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)))
      toast.success(`${user.name} ${next ? 'activated' : 'deactivated'}`)
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Update failed'))
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="py-16 text-center text-sm text-slate-500">Loading admin panel…</div>
      </div>
    )
  }

  const cards = [
    { label: 'Total users', value: stats?.total_users ?? 0, icon: Users },
    { label: 'Active users', value: stats?.active_users ?? 0, icon: ShieldCheck },
    { label: 'Resumes uploaded', value: stats?.total_resumes ?? 0, icon: Activity },
    { label: 'Analyses run', value: stats?.total_analyses ?? 0, icon: Activity },
    { label: 'Job matches', value: stats?.total_job_matches ?? 0, icon: Activity },
    {
      label: 'Avg ATS score',
      value: stats?.avg_ats_score != null ? `${stats.avg_ats_score}/100` : '—',
      icon: Activity,
    },
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Admin panel</h1>
          <p className="mt-1 text-sm text-slate-600">
            Platform analytics and user management.
          </p>
        </div>

        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{label}</p>
                <Icon className="h-4 w-4 text-brand-500" />
              </div>
              <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="text-sm font-semibold text-slate-900">Users</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Email</th>
                  <th className="px-5 py-3">Resumes</th>
                  <th className="px-5 py-3">Joined</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium text-slate-900">{u.name}</td>
                    <td className="px-5 py-3 text-slate-600">{u.email}</td>
                    <td className="px-5 py-3 text-slate-600">{u.resume_count}</td>
                    <td className="px-5 py-3 text-slate-600">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          u.is_superuser
                            ? 'bg-brand-50 text-brand-700'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {u.is_superuser ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Button
                        variant={u.is_active ? 'secondary' : 'primary'}
                        size="sm"
                        onClick={() => toggleActive(u)}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                      No users found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}
