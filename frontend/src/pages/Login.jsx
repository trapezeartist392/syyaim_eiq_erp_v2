import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'
import api from '../utils/api'
import { Factory, Eye, EyeOff } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState()
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const form = new URLSearchParams({ username: email, password })
      const { data } = await api.post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' }})
      login(data.user, data.access_token)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-[#0D1F3C] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 bg-yellow-500 rounded-2xl flex items-center justify-center mb-3 shadow-lg">
            <Factory size={28} className="text-slate-900" />
          </div>
          <h1 className="text-2xl font-bold text-white">Syyaim EIQ</h1>
          <p className="text-blue-300 text-sm mt-1">ERP Platform</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-lg font-bold text-slate-800 mb-6">Sign in to your account</h2>
          {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email address</label>
              <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="Enter email" />
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input className="input pr-10" type={showPass ? 'text' : 'password'}
                  value={password} onChange={e => setPassword(e.target.value)} required placeholder="Enter password" />
                <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  onClick={() => setShowPass(!showPass)}>
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full btn-primary justify-center py-2.5 mt-2 text-base">
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
          {/* <p className="text-xs text-slate-400 text-center mt-6">Default: admin@syyaimeiq.com / admin1234</p> */}
          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-500">
              Don't have an account?{" "}
              <a href="/signup" className="text-blue-700 font-medium hover:underline">Sign up</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
