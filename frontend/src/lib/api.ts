import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token } = response.data
          useAuthStore.getState().updateTokens(access_token, refresh_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch {
          useAuthStore.getState().logout()
          window.location.href = '/login'
        }
      } else {
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default api

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

// Users API
export const usersApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/users', { params }),
  get: (id: number) => api.get(`/users/${id}`),
  create: (data: { username: string; password: string; role: string }) =>
    api.post('/users', data),
  update: (id: number, data: { role?: string; is_active?: boolean }) =>
    api.put(`/users/${id}`, data),
  resetPassword: (id: number, password: string) =>
    api.post(`/users/${id}/reset-password`, { new_password: password }),
}

// Cases API
export const casesApi = {
  list: (params?: {
    page?: number
    page_size?: number
    category_id?: number
    risk_level?: string
    is_enabled?: boolean
    keyword?: string
  }) => api.get('/cases', { params }),
  get: (id: number) => api.get(`/cases/${id}`),
  create: (data: {
    name: string
    category_id: number
    risk_level: string
    script_path: string
    description?: string
    fix_suggestion?: string
  }) => api.post('/cases', data),
  update: (id: number, data: Partial<{
    name: string
    category_id: number
    risk_level: string
    script_path: string
    description: string
    fix_suggestion: string
    is_enabled: boolean
  }>) => api.put(`/cases/${id}`, data),
  delete: (id: number) => api.delete(`/cases/${id}`),
  toggle: (id: number) => api.post(`/cases/${id}/toggle`),
}

// Categories API
export const categoriesApi = {
  list: () => api.get('/categories'),
  get: (id: number) => api.get(`/categories/${id}`),
  create: (data: { name: string; description?: string; sort_order?: number }) =>
    api.post('/categories', data),
  update: (id: number, data: { name?: string; description?: string; sort_order?: number }) =>
    api.put(`/categories/${id}`, data),
  delete: (id: number) => api.delete(`/categories/${id}`),
  reorder: (orders: { id: number; sort_order: number }[]) =>
    api.post('/categories/reorder', { orders }),
}

// Tasks API
export const tasksApi = {
  list: (params?: {
    page?: number
    page_size?: number
    status?: string
    target_ip?: string
    my_tasks?: boolean
  }) => api.get('/tasks', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
  create: (data: { target_ip: string; description?: string; case_ids?: number[] }) =>
    api.post('/tasks', data),
  stop: (id: number) => api.post(`/tasks/${id}/stop`),
  retry: (id: number) => api.post(`/tasks/${id}/retry`),
  rerun: (id: number) => api.post(`/tasks/${id}/rerun`),
}

// Reports API
export const reportsApi = {
  get: (taskId: number) => api.get(`/reports/tasks/${taskId}`),
  exportJson: (taskId: number) =>
    api.get(`/reports/tasks/${taskId}/export/json`, { responseType: 'blob' }),
  exportHtml: (taskId: number) =>
    api.get(`/reports/tasks/${taskId}/export/html`, { responseType: 'blob' }),
}
