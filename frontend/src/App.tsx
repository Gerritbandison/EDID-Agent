import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Common/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import InventoryList from './components/Inventory/InventoryList'
import DeviceDetail from './components/Inventory/DeviceDetail'
import MonitorList from './components/Monitors/MonitorList'
import MonitorDetail from './components/Monitors/MonitorDetail'
import UserList from './components/Users/UserList'
import UserDetail from './components/Users/UserDetail'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/inventory" element={<InventoryList />} />
        <Route path="/devices/:deviceId" element={<DeviceDetail />} />
        <Route path="/monitors" element={<MonitorList />} />
        <Route path="/monitors/:monitorId" element={<MonitorDetail />} />
        <Route path="/users" element={<UserList />} />
        <Route path="/users/:username" element={<UserDetail />} />
      </Routes>
    </Layout>
  )
}

export default App
