import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import StatusIndicator from '../Common/StatusIndicator'
import type { DeviceStatus } from '../../types'

interface RecentDevice {
  id: string
  hostname: string
  assigned_user: string | null
  last_check_in: string | null
  status: DeviceStatus
}

interface RecentDevicesProps {
  devices: RecentDevice[]
}

export default function RecentDevices({ devices }: RecentDevicesProps) {
  if (devices.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No recent check-ins
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {devices.map((device) => (
        <Link
          key={device.id}
          to={`/devices/${device.id}`}
          className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <StatusIndicator status={device.status} />
            <div>
              <p className="font-medium text-gray-900 dark:text-white">
                {device.hostname}
              </p>
              <p className="text-sm text-gray-500">
                {device.assigned_user || 'Unassigned'}
              </p>
            </div>
          </div>
          <span className="text-sm text-gray-500">
            {device.last_check_in
              ? formatDistanceToNow(new Date(device.last_check_in), {
                  addSuffix: true,
                })
              : 'Never'}
          </span>
        </Link>
      ))}
    </div>
  )
}
