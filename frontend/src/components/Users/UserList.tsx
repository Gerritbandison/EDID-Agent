import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { Search, Users, Laptop, Building } from 'lucide-react'
import { usersApi } from '../../services/api'
import LoadingSpinner from '../Common/LoadingSpinner'

export default function UserList() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['users', { search, page }],
    queryFn: () =>
      usersApi.getUsers({
        search,
        page,
        per_page: 25,
      }),
  })

  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: usersApi.getDepartments,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Users
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {data?.pagination.total || 0} users with assigned devices
        </p>
      </div>

      {/* Departments Summary */}
      {departments && departments.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {departments.slice(0, 6).map((dept) => (
            <div key={dept.department} className="card text-center">
              <Building className="h-5 w-5 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {dept.department}
              </p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">
                {dept.user_count}
              </p>
              <p className="text-xs text-gray-500">users</p>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by username, email, or department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* User Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.users.map((user) => (
              <Link
                key={user.username}
                to={`/users/${encodeURIComponent(user.username)}`}
                className="card hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-green-100 dark:bg-green-900/50 rounded-lg">
                    <Users className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="flex items-center space-x-1 text-sm text-gray-500">
                    <Laptop className="h-4 w-4" />
                    <span>{user.device_count}</span>
                  </div>
                </div>

                <h3 className="font-medium text-gray-900 dark:text-white">
                  {user.username}
                </h3>

                {user.email && (
                  <p className="text-sm text-gray-500 truncate">{user.email}</p>
                )}

                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 text-sm text-gray-500">
                  <div className="flex items-center justify-between">
                    <span>{user.department || 'No department'}</span>
                    <span>
                      {user.last_activity
                        ? formatDistanceToNow(new Date(user.last_activity), {
                            addSuffix: true,
                          })
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {data?.users.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No users found
            </div>
          )}

          {/* Pagination */}
          {data?.pagination && data.pagination.total > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing {((page - 1) * 25) + 1} to{' '}
                {Math.min(page * 25, data.pagination.total)} of{' '}
                {data.pagination.total} users
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
