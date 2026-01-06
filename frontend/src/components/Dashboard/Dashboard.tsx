import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Laptop,
  Monitor,
  Users,
  Activity,
  AlertCircle,
  Clock,
  TrendingUp,
} from 'lucide-react'
import { inventoryApi, monitorsApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'
import StatusIndicator from '../Common/StatusIndicator'
import StatsCard from './StatsCard'
import ManufacturerChart from './ManufacturerChart'
import RecentDevices from './RecentDevices'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['inventory-stats'],
    queryFn: inventoryApi.getStats,
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: monitorStats, isLoading: monitorStatsLoading } = useQuery({
    queryKey: ['monitor-stats'],
    queryFn: monitorsApi.getStats,
  })

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Overview of your device inventory
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Devices"
          value={stats?.summary.total_devices || 0}
          icon={Laptop}
          color="blue"
          href="/inventory"
        />
        <StatsCard
          title="Connected Monitors"
          value={stats?.summary.total_monitors || 0}
          icon={Monitor}
          color="purple"
          href="/monitors"
        />
        <StatsCard
          title="Unique Users"
          value={stats?.summary.unique_users || 0}
          icon={Users}
          color="green"
          href="/users"
        />
        <StatsCard
          title="Recent Check-ins (24h)"
          value={stats?.summary.recent_check_ins_24h || 0}
          icon={Activity}
          color="orange"
        />
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/50 rounded-lg">
                <Activity className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Online</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats?.summary.online_devices || 0}
                </p>
              </div>
            </div>
            <StatusIndicator status="online" size="lg" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/50 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Idle</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats?.summary.idle_devices || 0}
                </p>
              </div>
            </div>
            <StatusIndicator status="idle" size="lg" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-100 dark:bg-red-900/50 rounded-lg">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Offline</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats?.summary.offline_devices || 0}
                </p>
              </div>
            </div>
            <StatusIndicator status="offline" size="lg" />
          </div>
        </div>
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Manufacturer Distribution */}
        <div className="card">
          <h3 className="card-header flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-gray-500" />
            <span>Devices by Manufacturer</span>
          </h3>
          <ManufacturerChart data={stats?.by_manufacturer || {}} />
        </div>

        {/* Recent Devices */}
        <div className="card">
          <h3 className="card-header flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-gray-500" />
              <span>Recent Check-ins</span>
            </span>
            <Link
              to="/inventory"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              View all
            </Link>
          </h3>
          <RecentDevices devices={stats?.recent_devices || []} />
        </div>
      </div>

      {/* OS Distribution */}
      {stats?.by_os && Object.keys(stats.by_os).length > 0 && (
        <div className="card">
          <h3 className="card-header">Operating Systems</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.by_os).map(([os, count]) => (
              <div
                key={os}
                className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <p className="text-sm text-gray-600 dark:text-gray-400">{os}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {count}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
