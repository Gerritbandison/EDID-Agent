import type { DeviceStatus } from '../../types'

interface StatusIndicatorProps {
  status: DeviceStatus
  showText?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const statusConfig = {
  online: {
    color: 'bg-green-500',
    textColor: 'text-green-600 dark:text-green-400',
    label: 'Online',
  },
  idle: {
    color: 'bg-yellow-500',
    textColor: 'text-yellow-600 dark:text-yellow-400',
    label: 'Idle',
  },
  offline: {
    color: 'bg-red-500',
    textColor: 'text-red-600 dark:text-red-400',
    label: 'Offline',
  },
  unknown: {
    color: 'bg-gray-400',
    textColor: 'text-gray-600 dark:text-gray-400',
    label: 'Unknown',
  },
}

const sizeConfig = {
  sm: 'h-2 w-2',
  md: 'h-3 w-3',
  lg: 'h-4 w-4',
}

export default function StatusIndicator({
  status,
  showText = false,
  size = 'md',
}: StatusIndicatorProps) {
  const config = statusConfig[status] || statusConfig.unknown

  return (
    <div className="flex items-center space-x-2">
      <span
        className={`inline-block rounded-full ${config.color} ${sizeConfig[size]}`}
        title={config.label}
      />
      {showText && (
        <span className={`text-sm font-medium ${config.textColor}`}>
          {config.label}
        </span>
      )}
    </div>
  )
}
