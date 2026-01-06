import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import {
  ArrowLeft,
  Monitor,
  Laptop,
  Calendar,
  Maximize,
  Plug,
  FileText,
} from 'lucide-react'
import { monitorsApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'

export default function MonitorDetail() {
  const { monitorId } = useParams<{ monitorId: string }>()

  const { data: monitor, isLoading } = useQuery({
    queryKey: ['monitor', monitorId],
    queryFn: () => monitorsApi.getMonitor(monitorId!),
    enabled: !!monitorId,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!monitor) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Monitor not found</p>
        <Link to="/monitors" className="text-primary-600 hover:text-primary-700">
          Back to Monitors
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Link
          to="/monitors"
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {monitor.manufacturer.name} {monitor.model_name}
            </h1>
            {monitor.status.is_primary && (
              <span className="text-xs bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 px-2 py-1 rounded">
                Primary
              </span>
            )}
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Serial: {monitor.serial_number || 'N/A'}
          </p>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
              <Maximize className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Resolution</p>
              <p className="font-medium">{monitor.display.native_resolution || 'Unknown'}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
              <Monitor className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Screen Size</p>
              <p className="font-medium">
                {monitor.display.diagonal_inches
                  ? `${monitor.display.diagonal_inches}"`
                  : 'Unknown'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/50 rounded-lg">
              <Calendar className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Age</p>
              <p className="font-medium">
                {monitor.manufacture_date.age_years !== null
                  ? `${monitor.manufacture_date.age_years} years`
                  : 'Unknown'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/50 rounded-lg">
              <Plug className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Connection</p>
              <p className="font-medium">{monitor.connection.type || 'Unknown'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Connected Device */}
      {monitor.device && (
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <Laptop className="h-5 w-5 text-gray-500" />
            <span>Connected Device</span>
          </h3>
          <Link
            to={`/devices/${monitor.device.id}`}
            className="block p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <p className="font-medium text-primary-600">{monitor.device.hostname}</p>
            {monitor.device.assigned_user && (
              <p className="text-sm text-gray-500">User: {monitor.device.assigned_user}</p>
            )}
          </Link>
        </div>
      )}

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Display Specs */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <Monitor className="h-5 w-5 text-gray-500" />
            <span>Display Specifications</span>
          </h3>
          <dl className="space-y-3">
            <DetailRow label="Native Resolution" value={monitor.display.native_resolution} />
            <DetailRow
              label="Dimensions"
              value={
                monitor.display.width && monitor.display.height
                  ? `${monitor.display.width} x ${monitor.display.height}`
                  : null
              }
            />
            <DetailRow label="Aspect Ratio" value={monitor.display.aspect_ratio} />
            <DetailRow
              label="Physical Size"
              value={
                monitor.display.screen_width_cm && monitor.display.screen_height_cm
                  ? `${monitor.display.screen_width_cm} x ${monitor.display.screen_height_cm} cm`
                  : null
              }
            />
            <DetailRow
              label="Diagonal"
              value={monitor.display.diagonal_inches ? `${monitor.display.diagonal_inches}"` : null}
            />
            <DetailRow
              label="Color Depth"
              value={monitor.display.color_bit_depth ? `${monitor.display.color_bit_depth}-bit` : null}
            />
            <DetailRow
              label="HDR Support"
              value={monitor.display.hdr_supported ? 'Yes' : 'No'}
            />
          </dl>
        </div>

        {/* Manufacturer Info */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <FileText className="h-5 w-5 text-gray-500" />
            <span>Manufacturer Information</span>
          </h3>
          <dl className="space-y-3">
            <DetailRow label="Manufacturer" value={monitor.manufacturer.name} />
            <DetailRow label="Manufacturer ID" value={monitor.manufacturer.id} mono />
            <DetailRow label="Product Code" value={monitor.manufacturer.product_code} mono />
            <DetailRow label="Model Name" value={monitor.model_name} />
            <DetailRow label="Serial Number" value={monitor.serial_number} mono />
            <DetailRow label="Manufacture Date" value={monitor.manufacture_date.formatted} />
            <DetailRow label="Manufacture Week" value={monitor.manufacture_date.week?.toString()} />
            <DetailRow label="Manufacture Year" value={monitor.manufacture_date.year?.toString()} />
          </dl>
        </div>

        {/* Timing */}
        <div className="card">
          <h3 className="card-header">Timing Specifications</h3>
          <dl className="space-y-3">
            <DetailRow
              label="Max Horizontal Freq"
              value={monitor.timing.max_horizontal_freq_khz ? `${monitor.timing.max_horizontal_freq_khz} kHz` : null}
            />
            <DetailRow
              label="Max Vertical Freq"
              value={monitor.timing.max_vertical_freq_hz ? `${monitor.timing.max_vertical_freq_hz} Hz` : null}
            />
            <DetailRow
              label="Max Pixel Clock"
              value={monitor.timing.max_pixel_clock_mhz ? `${monitor.timing.max_pixel_clock_mhz} MHz` : null}
            />
          </dl>
        </div>

        {/* Connection */}
        <div className="card">
          <h3 className="card-header">Connection Details</h3>
          <dl className="space-y-3">
            <DetailRow label="Connection Type" value={monitor.connection.type} />
            <DetailRow label="Port" value={monitor.connection.port} />
            <DetailRow label="EDID Version" value={monitor.edid.version} />
            <DetailRow label="Is Primary" value={monitor.status.is_primary ? 'Yes' : 'No'} />
            <DetailRow label="Is Connected" value={monitor.status.is_connected ? 'Yes' : 'No'} />
          </dl>
        </div>
      </div>

      {/* Supported Resolutions */}
      {monitor.supported_resolutions && monitor.supported_resolutions.length > 0 && (
        <div className="card">
          <h3 className="card-header">Supported Resolutions</h3>
          <div className="flex flex-wrap gap-2">
            {monitor.supported_resolutions.map((res, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm"
              >
                {res}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div className="card">
        <h3 className="card-header">Timeline</h3>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">First Seen</dt>
            <dd>
              {monitor.timestamps.first_seen
                ? format(new Date(monitor.timestamps.first_seen), 'PPp')
                : 'N/A'}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Seen</dt>
            <dd>
              {monitor.timestamps.last_seen
                ? format(new Date(monitor.timestamps.last_seen), 'PPp')
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
