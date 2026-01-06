import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow, format } from 'date-fns'
import {
  ArrowLeft,
  Laptop,
  Monitor,
  User,
  Cpu,
  HardDrive,
  Network,
  Activity,
} from 'lucide-react'
import { devicesApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'
import StatusIndicator from '../Common/StatusIndicator'
import type { DeviceStatus } from '../../types'

export default function DeviceDetail() {
  const { deviceId } = useParams<{ deviceId: string }>()

  const { data: device, isLoading } = useQuery({
    queryKey: ['device', deviceId],
    queryFn: () => devicesApi.getDevice(deviceId!),
    enabled: !!deviceId,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!device) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Device not found</p>
        <Link to="/inventory" className="text-primary-600 hover:text-primary-700">
          Back to Inventory
        </Link>
      </div>
    )
  }

  const status = device.agent_status?.connection_status as DeviceStatus || 'unknown'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Link
          to="/inventory"
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {device.hostname}
            </h1>
            <StatusIndicator status={status} showText />
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            {device.manufacturer} {device.model}
          </p>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
              <Laptop className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Serial Number</p>
              <p className="font-medium">{device.serial_number || 'N/A'}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/50 rounded-lg">
              <User className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Assigned User</p>
              {device.user.assigned_user ? (
                <Link
                  to={`/users/${device.user.assigned_user}`}
                  className="font-medium text-primary-600 hover:text-primary-700"
                >
                  {device.user.assigned_user}
                </Link>
              ) : (
                <p className="font-medium text-gray-400">Unassigned</p>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
              <Monitor className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Connected Monitors</p>
              <p className="font-medium">{device.monitors?.length || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/50 rounded-lg">
              <Activity className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Last Check-in</p>
              <p className="font-medium">
                {device.timestamps.last_check_in
                  ? formatDistanceToNow(new Date(device.timestamps.last_check_in), {
                      addSuffix: true,
                    })
                  : 'Never'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hardware */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <Cpu className="h-5 w-5 text-gray-500" />
            <span>Hardware</span>
          </h3>
          <dl className="space-y-3">
            <DetailRow label="Manufacturer" value={device.manufacturer} />
            <DetailRow label="Model" value={device.model} />
            <DetailRow label="CPU" value={device.hardware.cpu_model} />
            <DetailRow
              label="Cores / Threads"
              value={
                device.hardware.cpu_cores
                  ? `${device.hardware.cpu_cores} / ${device.hardware.cpu_threads}`
                  : null
              }
            />
            <DetailRow
              label="RAM"
              value={device.hardware.ram_total_gb ? `${device.hardware.ram_total_gb} GB` : null}
            />
          </dl>
        </div>

        {/* Storage */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <HardDrive className="h-5 w-5 text-gray-500" />
            <span>Storage & OS</span>
          </h3>
          <dl className="space-y-3">
            <DetailRow
              label="Storage"
              value={
                device.hardware.storage_total_gb
                  ? `${device.hardware.storage_total_gb} GB ${device.hardware.storage_type || ''}`
                  : null
              }
            />
            <DetailRow label="Operating System" value={device.os.name} />
            <DetailRow label="OS Version" value={device.os.version} />
            <DetailRow label="OS Build" value={device.os.build} />
            <DetailRow label="Architecture" value={device.os.architecture} />
          </dl>
        </div>

        {/* Network */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <Network className="h-5 w-5 text-gray-500" />
            <span>Network</span>
          </h3>
          <dl className="space-y-3">
            <DetailRow label="IP Address" value={device.network.ip_address} />
            <DetailRow label="MAC Address" value={device.network.mac_address} mono />
            <DetailRow label="Domain" value={device.user.domain} />
          </dl>
        </div>

        {/* Directory Info */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <User className="h-5 w-5 text-gray-500" />
            <span>Directory Information</span>
          </h3>
          <dl className="space-y-3">
            <DetailRow label="User Email" value={device.user.email} />
            <DetailRow label="Department" value={device.department} />
            <DetailRow label="Location" value={device.location} />
            <DetailRow label="Organizational Unit" value={device.directory_info.ad_organizational_unit} />
          </dl>
        </div>
      </div>

      {/* Connected Monitors */}
      {device.monitors && device.monitors.length > 0 && (
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <Monitor className="h-5 w-5 text-gray-500" />
            <span>Connected Monitors</span>
          </h3>
          <div className="space-y-4">
            {device.monitors.map((monitor) => (
              <Link
                key={monitor.id}
                to={`/monitors/${monitor.id}`}
                className="block p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {monitor.manufacturer.name} {monitor.model_name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {monitor.display.native_resolution} • {monitor.display.diagonal_inches}"
                      {monitor.status.is_primary && (
                        <span className="ml-2 text-xs bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 px-2 py-0.5 rounded">
                          Primary
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <p>{monitor.connection.type}</p>
                    <p>Year: {monitor.manufacture_date.year}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Agent Status */}
      {device.agent_status && (
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <Activity className="h-5 w-5 text-gray-500" />
            <span>Agent Status</span>
          </h3>
          <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <dt className="text-sm text-gray-500">Version</dt>
              <dd className="font-medium">{device.agent_status.agent_version || 'Unknown'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Platform</dt>
              <dd className="font-medium capitalize">{device.agent_status.agent_platform || 'Unknown'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Total Check-ins</dt>
              <dd className="font-medium">{device.agent_status.statistics.total_check_ins}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Success Rate</dt>
              <dd className="font-medium">{device.agent_status.statistics.success_rate}%</dd>
            </div>
          </dl>
        </div>
      )}

      {/* Timestamps */}
      <div className="card">
        <h3 className="card-header">Timeline</h3>
        <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">First Seen</dt>
            <dd>
              {device.timestamps.first_seen
                ? format(new Date(device.timestamps.first_seen), 'PPp')
                : 'N/A'}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Check-in</dt>
            <dd>
              {device.timestamps.last_check_in
                ? format(new Date(device.timestamps.last_check_in), 'PPp')
                : 'N/A'}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Created</dt>
            <dd>
              {device.timestamps.created_at
                ? format(new Date(device.timestamps.created_at), 'PPp')
                : 'N/A'}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Updated</dt>
            <dd>
              {device.timestamps.updated_at
                ? format(new Date(device.timestamps.updated_at), 'PPp')
                : 'N/A'}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  )
}

function DetailRow({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string | null | undefined
  mono?: boolean
}) {
  return (
    <div className="flex justify-between">
      <dt className="text-gray-500">{label}</dt>
      <dd className={`text-right ${mono ? 'font-mono text-sm' : ''}`}>
        {value || <span className="text-gray-400">N/A</span>}
      </dd>
    </div>
  )
}
