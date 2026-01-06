import { useState, Fragment } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import {
  Search,
  Download,
  ChevronDown,
  ChevronUp,
  Monitor,
  ArrowUpDown,
} from 'lucide-react'
import { inventoryApi, devicesApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'
import StatusIndicator from '../Common/StatusIndicator'
import type { Device, DeviceStatus } from '../../types'

export default function InventoryList() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string>('')
  const [manufacturer, setManufacturer] = useState<string>('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('last_check_in')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['inventory', { search, status, manufacturer, page, sortBy, sortOrder }],
    queryFn: () =>
      inventoryApi.getInventory({
        search,
        status: status || undefined,
        page,
        per_page: 25,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  })

  const { data: manufacturers } = useQuery({
    queryKey: ['manufacturers'],
    queryFn: devicesApi.getManufacturers,
  })

  const toggleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedRows(newExpanded)
  }

  const handleExport = async () => {
    try {
      const blob = await inventoryApi.exportInventory('csv')
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'inventory_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Device Inventory
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {data?.pagination.total || 0} devices total
          </p>
        </div>
        <button onClick={handleExport} className="btn btn-secondary flex items-center space-x-2">
          <Download className="h-4 w-4" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by hostname, serial, user..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="input w-full md:w-40"
          >
            <option value="">All Status</option>
            <option value="online">Online</option>
            <option value="idle">Idle</option>
            <option value="offline">Offline</option>
          </select>
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
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-8"></th>
                  <th>
                    <button
                      onClick={() => toggleSort('hostname')}
                      className="flex items-center space-x-1 hover:text-gray-900 dark:hover:text-white"
                    >
                      <span>Hostname</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </button>
                  </th>
                  <th>User</th>
                  <th>Model</th>
                  <th className="text-center">Monitors</th>
                  <th>Status</th>
                  <th>
                    <button
                      onClick={() => toggleSort('last_check_in')}
                      className="flex items-center space-x-1 hover:text-gray-900 dark:hover:text-white"
                    >
                      <span>Last Seen</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.inventory.map((device) => (
                  <Fragment key={device.id}>
                    <tr
                      className="cursor-pointer"
                      onClick={() => toggleRow(device.id)}
                    >
                      <td>
                        {expandedRows.has(device.id) ? (
                          <ChevronUp className="h-4 w-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-gray-400" />
                        )}
                      </td>
                      <td>
                        <Link
                          to={`/devices/${device.id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="font-medium text-primary-600 hover:text-primary-700"
                        >
                          {device.hostname}
                        </Link>
                        {device.serial_number && (
                          <p className="text-xs text-gray-500">
                            SN: {device.serial_number}
                          </p>
                        )}
                      </td>
                      <td>
                        {device.user.assigned_user ? (
                          <Link
                            to={`/users/${device.user.assigned_user}`}
                            onClick={(e) => e.stopPropagation()}
                            className="hover:text-primary-600"
                          >
                            {device.user.assigned_user}
                          </Link>
                        ) : (
                          <span className="text-gray-400">Unassigned</span>
                        )}
                      </td>
                      <td>
                        <span>{device.manufacturer || 'Unknown'}</span>
                        {device.model && (
                          <p className="text-xs text-gray-500">{device.model}</p>
                        )}
                      </td>
                      <td className="text-center">
                        <div className="flex items-center justify-center space-x-1">
                          <Monitor className="h-4 w-4 text-gray-400" />
                          <span>{device.monitor_count || 0}</span>
                        </div>
                      </td>
                      <td>
                        <StatusIndicator
                          status={device.status as DeviceStatus}
                          showText
                        />
                      </td>
                      <td className="text-gray-500">
                        {device.timestamps.last_check_in
                          ? formatDistanceToNow(
                              new Date(device.timestamps.last_check_in),
                              { addSuffix: true }
                            )
                          : 'Never'}
                      </td>
                    </tr>
                    {expandedRows.has(device.id) && (
                      <tr>
                        <td colSpan={7} className="bg-gray-50 dark:bg-gray-800/50 p-4">
                          <DeviceExpandedRow device={device} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data?.pagination && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing {((page - 1) * 25) + 1} to{' '}
                {Math.min(page * 25, data.pagination.total)} of{' '}
                {data.pagination.total} results
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

function DeviceExpandedRow({ device }: { device: Device }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <h4 className="font-medium text-gray-900 dark:text-white mb-2">
          Hardware
        </h4>
        <dl className="space-y-1 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">CPU</dt>
            <dd>{device.hardware.cpu_model || 'N/A'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">RAM</dt>
            <dd>{device.hardware.ram_total_gb ? `${device.hardware.ram_total_gb} GB` : 'N/A'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Storage</dt>
            <dd>
              {device.hardware.storage_total_gb
                ? `${device.hardware.storage_total_gb} GB ${device.hardware.storage_type || ''}`
                : 'N/A'}
            </dd>
          </div>
        </dl>
      </div>
      <div>
        <h4 className="font-medium text-gray-900 dark:text-white mb-2">
          Operating System
        </h4>
        <dl className="space-y-1 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">OS</dt>
            <dd>{device.os.name || 'N/A'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Version</dt>
            <dd>{device.os.version || 'N/A'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Architecture</dt>
            <dd>{device.os.architecture || 'N/A'}</dd>
          </div>
        </dl>
      </div>
      <div>
        <h4 className="font-medium text-gray-900 dark:text-white mb-2">
          Network
        </h4>
        <dl className="space-y-1 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">IP Address</dt>
            <dd>{device.network.ip_address || 'N/A'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">MAC Address</dt>
            <dd className="font-mono text-xs">{device.network.mac_address || 'N/A'}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
