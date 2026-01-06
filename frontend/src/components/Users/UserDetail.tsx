import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import {
  ArrowLeft,
  User,
  Laptop,
  Monitor,
  Download,
  Mail,
  Building,
} from 'lucide-react'
import { usersApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'
import StatusIndicator from '../Common/StatusIndicator'
import type { DeviceStatus } from '../../types'

export default function UserDetail() {
  const { username } = useParams<{ username: string }>()

  const { data, isLoading } = useQuery({
    queryKey: ['user', username],
    queryFn: () => usersApi.getUserDevices(decodeURIComponent(username!)),
    enabled: !!username,
  })

  const handleExport = async () => {
    if (!username) return
    try {
      const blob = await usersApi.exportUserAssets(decodeURIComponent(username))
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${username}_assets.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">User not found</p>
        <Link to="/users" className="text-primary-600 hover:text-primary-700">
          Back to Users
        </Link>
      </div>
    )
  }

  const { user, devices, summary } = data

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/users"
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {user.username}
            </h1>
            {user.email && (
              <p className="text-gray-600 dark:text-gray-400">{user.email}</p>
            )}
          </div>
        </div>
        <button onClick={handleExport} className="btn btn-secondary flex items-center space-x-2">
          <Download className="h-4 w-4" />
          <span>Export Assets</span>
        </button>
      </div>

      {/* User Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
              <Laptop className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Devices</p>
              <p className="text-2xl font-bold">{summary.total_devices}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
              <Monitor className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Monitors</p>
              <p className="text-2xl font-bold">{summary.total_monitors}</p>
            </div>
          </div>
        </div>

        {user.department && (
          <div className="card">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/50 rounded-lg">
                <Building className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Department</p>
                <p className="font-medium truncate">{user.department}</p>
              </div>
            </div>
          </div>
        )}

        {user.domain && (
          <div className="card">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/50 rounded-lg">
                <User className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Domain</p>
                <p className="font-medium truncate">{user.domain}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Devices */}
      <div className="card">
        <h3 className="card-header flex items-center space-x-2">
          <Laptop className="h-5 w-5 text-gray-500" />
          <span>Assigned Devices</span>
        </h3>
        <div className="space-y-4">
          {devices.map((device) => (
            <div
              key={device.id}
              className="p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50"
            >
              <div className="flex items-center justify-between mb-3">
                <Link
                  to={`/devices/${device.id}`}
                  className="font-medium text-primary-600 hover:text-primary-700"
                >
                  {device.hostname}
                </Link>
                <StatusIndicator
                  status={device.status as DeviceStatus}
                  showText
                />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Model</p>
                  <p>{device.manufacturer} {device.model}</p>
                </div>
                <div>
                  <p className="text-gray-500">Serial</p>
                  <p className="font-mono">{device.serial_number || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">OS</p>
                  <p>{device.os || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Last Seen</p>
                  <p>
                    {device.last_check_in
                      ? formatDistanceToNow(new Date(device.last_check_in), {
                          addSuffix: true,
                        })
                      : 'Never'}
                  </p>
                </div>
              </div>

              {/* Device Monitors */}
              {device.monitors && device.monitors.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                  <p className="text-sm text-gray-500 mb-2">
                    Connected Monitors ({device.monitor_count})
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {device.monitors.map((monitor) => (
                      <Link
                        key={monitor.id}
                        to={`/monitors/${monitor.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1 bg-white dark:bg-gray-800 rounded-full text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <Monitor className="h-3 w-3 text-gray-400" />
                        <span>
                          {monitor.manufacturer.name} {monitor.display.native_resolution}
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {devices.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No devices assigned to this user
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
