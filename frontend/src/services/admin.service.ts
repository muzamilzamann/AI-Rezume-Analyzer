import { api } from '@/lib/api'
import type { AdminStats, AdminUserRead } from '@/types'

export const adminService = {
  stats(): Promise<AdminStats> {
    return api.get<AdminStats>('/admin/stats').then((res) => res.data)
  },
  users(): Promise<AdminUserRead[]> {
    return api.get<AdminUserRead[]>('/admin/users').then((res) => res.data)
  },
  setUserActive(id: string, is_active: boolean): Promise<AdminUserRead> {
    return api
      .patch<AdminUserRead>(`/admin/users/${id}`, { is_active })
      .then((res) => res.data)
  },
}
