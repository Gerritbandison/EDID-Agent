import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { Search, Monitor, Calendar } from 'lucide-react'
import { monitorsApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'

export default function MonitorList() {
  const [search, setSearch] = useState('')
  const [manufacturer, setManufacturer] = useState('')
  const [ageFilter, setAgeFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['monitors', { search, manufacturer, ageFilter, page }],
    queryFn: () => {
      const params: any = {
        search,
        page,
        per_page: 25,
        connected_only: true,
      }
      if (manufacturer) params.manufacturer = manufacturer
      if (ageFilter === 'old') params.min_age_years = 5
      if (ageFilter === 'new') params.max_age_years = 2
      return monitorsApi.getMonitors(params)
    },
  })

  const { data: manufacturers } = useQuery({
    queryKey: ['monitor-manufacturers'],
    queryFn: monitorsApi.getManufacturers,
  })

  const { data: stats } = useQuery({
    queryKey: ['monitor-stats'],
    queryFn: monitorsApi.getStats,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Monitors
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {stats?.total || 0} connected monitors
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats.by_age).map(([range, count]) => (
            <div key={range} className="card text-center">
              <p className="text-sm text-gray-500">{range}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {count}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by model, serial, manufacturer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={manufacturer}
            onChange={(e) => setManufacturer(e.target.value)}
            className="input w-full md:w-48"
          >
            <option value="">All Manufacturers</option>
            {manufacturers?.map((mfg) => (
              <option key={mfg} value={mfg}>
                {mfg}
              </option>
            ))}
          </select>
          <select
            value={ageFilter}
            onChange={(e) => setAgeFilter(e.target.value)}
            className="input w-full md:w-40"
          >
            <option value="">All Ages</option>
            <option value="new">0-2 years</option>
            <option value="old">5+ years</option>
          </select>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.monitors.map((monitor) => (
              <Link
                key={monitor.id}
                to={`/monitors/${monitor.id}`}
                className="card hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
                    <Monitor className="h-6 w-6 text-purple-600" />
                  </div>
                  {monitor.status.is_primary && (
                    <span className="text-xs bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 px-2 py-1 rounded">
                      Primary
                    </span>
                  )}
                </div>

                <h3 className="font-medium text-gray-900 dark:text-white">
                  {monitor.manufacturer.name || 'Unknown'} {monitor.model_name}
                </h3>

                <p className="text-sm text-gray-500 mt-1">
                  {monitor.display.native_resolution} •{' '}
                  {monitor.display.diagonal_inches
                    ? `${monitor.display.diagonal_inches}"`
                    : 'Size unknown'}
                </p>

                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">
                      {monitor.connection.type || 'Unknown'}
                    </span>
                    <span className="flex items-center space-x-1 text-gray-500">
                      <Calendar className="h-4 w-4" />
                      <span>
                        {monitor.manufacture_date.year
                          ? `${monitor.manufacture_date.age_years}y old`
                          : 'Age unknown'}
                      </span>
                    </span>
                  </div>

                  {monitor.device && (
                    <p className="text-sm text-gray-500 mt-2">
                      Connected to: {monitor.device.hostname}
                    </p>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {data?.pagination && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing {((page - 1) * 25) + 1} to{' '}
                {Math.min(page * 25, data.pagination.total)} of{' '}
                {data.pagination.total} monitors
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!data.pagination.has_prev}
                  className="btn btn-secondary disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.pagination.has_next}
                  className="btn btn-secondary disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
