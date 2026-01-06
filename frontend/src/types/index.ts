export interface Device {
  id: string
  hostname: string
  serial_number: string | null
  model: string | null
  manufacturer: string | null
  hardware: {
    cpu_model: string | null
    cpu_cores: number | null
    cpu_threads: number | null
    ram_total_gb: number | null
    storage_total_gb: number | null
    storage_type: string | null
  }
  os: {
    name: string | null
    version: string | null
    build: string | null
    architecture: string | null
  }
  network: {
    ip_address: string | null
    mac_address: string | null
  }
  user: {
    assigned_user: string | null
    email: string | null
    domain: string | null
  }
  directory_info: {
    ad_distinguished_name: string | null
    ad_organizational_unit: string | null
    entra_device_id: string | null
    entra_tenant_id: string | null
  }
  location: string | null
  department: string | null
  timestamps: {
    first_seen: string | null
    last_check_in: string | null
    created_at: string | null
    updated_at: string | null
  }
  monitors?: Monitor[]
  monitor_count?: number
  agent_status?: AgentStatus
  status?: DeviceStatus
  status_color?: StatusColor
}

export interface Monitor {
  id: string
  device_id: string
  manufacturer: {
    id: string | null
    name: string | null
    product_code: string | null
  }
  serial_number: string | null
  model_name: string | null
  manufacture_date: {
    week: number | null
    year: number | null
    formatted: string | null
    age_years: number | null
  }
  display: {
    native_resolution: string | null
    width: number | null
    height: number | null
    screen_width_cm: number | null
    screen_height_cm: number | null
    diagonal_inches: number | null
    aspect_ratio: string | null
    color_bit_depth: number | null
    hdr_supported: boolean
  }
  timing: {
    max_horizontal_freq_khz: number | null
    max_vertical_freq_hz: number | null
    max_pixel_clock_mhz: number | null
  }
  connection: {
    type: string | null
    port: string | null
  }
  edid: {
    version: string | null
    raw: string | null
  }
  supported_resolutions: string[]
  status: {
    is_primary: boolean
    is_connected: boolean
  }
  timestamps: {
    first_seen: string | null
    last_seen: string | null
  }
  device?: {
    id: string
    hostname: string
    assigned_user: string | null
  }
}

export interface AgentStatus {
  device_id: string
  agent_version: string | null
  agent_platform: string | null
  connection_status: string
  last_heartbeat: string | null
  last_successful_sync: string | null
  statistics: {
    total_check_ins: number
    successful_check_ins: number
    failed_check_ins: number
    success_rate: number
    consecutive_failures: number
  }
  check_in_interval_seconds: number
  last_error: string | null
  last_error_time: string | null
}

export type DeviceStatus = 'online' | 'idle' | 'offline' | 'unknown'
export type StatusColor = 'green' | 'yellow' | 'red' | 'gray'

export interface InventoryStats {
  summary: {
    total_devices: number
    online_devices: number
    idle_devices: number
    offline_devices: number
    total_monitors: number
    unique_users: number
    recent_check_ins_24h: number
  }
  by_manufacturer: Record<string, number>
  by_model: Array<{ model: string; manufacturer: string; count: number }>
  by_os: Record<string, number>
  recent_devices: Array<{
    id: string
    hostname: string
    assigned_user: string | null
    last_check_in: string | null
    status: DeviceStatus
  }>
}

export interface MonitorStats {
  total: number
  by_manufacturer: Record<string, number>
  by_age: Record<string, number>
  by_resolution: Record<string, number>
}

export interface User {
  username: string
  email: string | null
  domain: string | null
  department: string | null
  device_count: number
  last_activity: string | null
}

export interface Pagination {
  page: number
  per_page: number
  total: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface PaginatedResponse<T> {
  pagination: Pagination
}

export interface InventoryResponse extends PaginatedResponse<Device> {
  inventory: Device[]
}

export interface DeviceResponse extends PaginatedResponse<Device> {
  devices: Device[]
}

export interface MonitorResponse extends PaginatedResponse<Monitor> {
  monitors: Monitor[]
}

export interface UserResponse extends PaginatedResponse<User> {
  users: User[]
}
