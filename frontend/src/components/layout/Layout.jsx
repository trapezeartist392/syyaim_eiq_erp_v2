import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../store/auth'
import { LayoutDashboard, Users, ShoppingCart, Package, UserCog, DollarSign, Bot, LogOut, Cpu } from 'lucide-react'
import TrialBanner from '../TrialBanner'
import clsx from 'clsx'

const nav = [
  { to: '/',        icon: LayoutDashboard, label: 'Dashboard',   end: true },
  { to: '/crm',     icon: Users,           label: 'CRM & Sales' },
  { to: '/purchase',icon: ShoppingCart,    label: 'Purchase' },
  { to: '/material',icon: Package,         label: 'Material' },
  { to: '/hr',      icon: UserCog,         label: 'HR & Payroll' },
  { to: '/finance', icon: DollarSign,      label: 'Finance' },
  { to: '/agents',  icon: Bot,             label: 'AI Agents' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-60 bg-[#0D1F3C] text-white flex flex-col shrink-0">
        <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
          <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center">
            <Cpu size={18} className="text-slate-900" />
          </div>
          <div>
            <div className="font-bold text-sm leading-tight">Syyaim EIQ</div>
            <div className="text-[10px] text-blue-300 uppercase tracking-wider">ERP Platform</div>
          </div>
        </div>

        <nav className="flex-1 py-4 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) =>
              clsx('flex items-center gap-3 px-5 py-2.5 text-sm transition-colors',
                isActive ? 'bg-white/10 text-white font-semibold border-r-2 border-yellow-400'
                         : 'text-blue-200 hover:bg-white/5 hover:text-white')}>
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium truncate">{user?.full_name}</div>
              <div className="text-[10px] text-blue-300 capitalize">{user?.role?.replace(/_/g,' ')}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="flex items-center gap-2 text-xs text-blue-300 hover:text-white w-full transition-colors">
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Trial / billing banner */}
        <TrialBanner />
        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
