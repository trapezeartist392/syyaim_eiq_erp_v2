import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './store/auth'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import CRM from './pages/CRM'
import Purchase from './pages/Purchase'
import Material from './pages/Material'
import HR from './pages/HR'
import Finance from './pages/Finance'
import Agents from './pages/Agents'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login"  element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected */}
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index         element={<Dashboard />} />
          <Route path="crm"      element={<CRM />} />
          <Route path="purchase" element={<Purchase />} />
          <Route path="material" element={<Material />} />
          <Route path="hr"       element={<HR />} />
          <Route path="finance"  element={<Finance />} />
          <Route path="agents"   element={<Agents />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
