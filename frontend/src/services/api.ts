import axios from 'axios'
import type {
  Device,
  Monitor,
  InventoryStats,
  MonitorStats,
  InventoryResponse,
  DeviceResponse,
  MonitorResponse,
  UserResponse,
  User,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Inventory API
export const inventoryApi = {
  getInventory: async (params?: {
    page?: number
    per_page?: number
    search?: string
    status?: string
    sort_by?: string
    sort_order?: string
  }): Promise<InventoryResponse> => {
    const { data } = await api.get('/inventory', { params })
    return data
  },

  getStats: async (): Promise<InventoryStats> => {
    const { data } = await api.get('/inventory/stats')
    return data
  },

  exportInventory: async (format: string = 'csv'): Promise<Blob> => {
    const { data } = await api.get('/inventory/export', {
      params: { format },
      responseType: 'blob',
    })
    return data
  },
}

// Devices API
export const devicesApi = {
  getDevices: async (params?: {
    page?: number
    per_page?: number
    search?: string
    manufacturer?: string
    status?: string
    sort_by?: string
    sort_order?: string
  }): Promise<DeviceResponse> => {
    const { data } = await api.get('/devices', { params })
    return data
  },

  getDevice: async (deviceId: string): Promise<Device> => {
    const { data } = await api.get(`/devices/${deviceId}`)
    return data
  },

  getManufacturers: async (): Promise<string[]> => {
    const { data } = await api.get('/devices/manufacturers')
    return data
  },

  getModels: async (manufacturer?: string): Promise<Array<{ model: string; manufacturer: string }>> => {
    const { data } = await api.get('/devices/models', {
      params: manufacturer ? { manufacturer } : {},
    })
    return data
  },
}

// Monitors API
export const monitorsApi = {
  getMonitors: async (params?: {
    page?: number
    per_page?: number
    search?: string
    manufacturer?: string
    min_age_years?: number
    max_age_years?: number
    connected_only?: boolean
  }): Promise<MonitorResponse> => {
    const { data } = await api.get('/monitors', { params })
    return data
  },

  getMonitor: async (monitorId: string): Promise<Monitor> => {
    const { data } = await api.get(`/monitors/${monitorId}`)
    return data
  },

  getManufacturers: async (): Promise<string[]> => {
    const { data } = await api.get('/monitors/manufacturers')
    return data
  },

  getStats: async (): Promise<MonitorStats> => {
    const { data } = await api.get('/monitors/stats')
    return data
  },
}

// Users API
export const usersApi = {
  getUsers: async (params?: {
    page?: number
    per_page?: number
    search?: string
  }): Promise<UserResponse> => {
    const { data } = await api.get('/users', { params })
    return data
  },

  getUserDevices: async (username: string): Promise<{
    user: User
    devices: Device[]
    summary: { total_devices: number; total_monitors: number }
  }> => {
    const { data } = await api.get(`/users/${encodeURIComponent(username)}`)
    return data
  },

  getDepartments: async (): Promise<Array<{
    department: string
    device_count: number
    user_count: number
  }>> => {
    const { data } = await api.get('/users/departments')
    return data
  },

  exportUserAssets: async (username: string): Promise<Blob> => {
    const { data } = await api.get(`/users/${encodeURIComponent(username)}/export`, {
      responseType: 'blob',
    })
    return data
  },
}

// Health API
export const healthApi = {
  check: async (): Promise<{ status: string; timestamp: string }> => {
    const { data } = await api.get('/health')
    return data
  },
}

export default api
