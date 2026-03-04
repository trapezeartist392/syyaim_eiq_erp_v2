import { useEffect, useState } from 'react'
import api from '../utils/api'
import { TrendingUp, ShoppingCart, Package, Users, DollarSign, Bot, AlertTriangle, BarChart3 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const fmt = (n) => n >= 100000 ? `₹${(n/100000).toFixed(1)}L` : `₹${n?.toLocaleString('en-IN') || 0}`

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [agentStats, setAgentStats] = useState(null)

  useEffect(() => {
    api.get('/dashboard/summary').then(r => setData(r.data)).catch(() => {})
    api.get('/agents/stats').then(r => setAgentStats(r.data)).catch(() => {})
  }, [])

  const metrics = data ? [
    { label: 'Pipeline Value', value: fmt(data.pipeline_value), icon: TrendingUp, color: 'bg-blue-500', sub: `${data.total_leads} leads` },
    { label: 'Pending PRs', value: data.pending_prs, icon: ShoppingCart, color: 'bg-orange-500', sub: 'Awaiting approval', alert: data.pending_prs > 0 },
    { label: 'Low Stock Items', value: data.low_stock_items, icon: Package, color: 'bg-red-500', sub: 'Below reorder point', alert: data.low_stock_items > 0 },
    { label: 'Employees', value: data.total_employees, icon: Users, color: 'bg-purple-500', sub: 'Active headcount' },
    { label: 'Net P&L', value: fmt(data.net_profit), icon: DollarSign, color: data.net_profit >= 0 ? 'bg-green-500' : 'bg-red-500', sub: `Income: ${fmt(data.total_income)}` },
    { label: 'AI Agent Actions', value: agentStats?.total_agent_actions || 0, icon: Bot, color: 'bg-yellow-500', sub: `${agentStats?.success_rate || 0}% success rate` },
  ] : []

  const chartData = data ? [
    { name: 'Income', value: data.total_income || 0, fill: '#22c55e' },
    { name: 'Expenses', value: (data.total_income || 0) - (data.net_profit || 0), fill: '#ef4444' },
    { name: 'Net Profit', value: Math.max(0, data.net_profit || 0), fill: '#3b82f6' },
  ] : []

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">Business overview — {new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })}</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 px-3 py-1.5 rounded-full text-xs font-medium">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          All systems operational
        </div>
      </div>

      {/* KPI grid */}
      {data ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics.map((m) => (
            <div key={m.label} className="card p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-slate-500 font-medium">{m.label}</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">{m.value}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{m.sub}</p>
                </div>
                <div className={`w-10 h-10 ${m.color} rounded-xl flex items-center justify-center shrink-0`}>
                  <m.icon size={20} className="text-white" />
                </div>
              </div>
              {m.alert && (
                <div className="mt-3 flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-md">
                  <AlertTriangle size={12} /> Needs attention
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <div key={i} className="card p-5 h-28 animate-pulse bg-slate-100" />)}
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-6">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={18} className="text-blue-600" />
            <h3 className="font-semibold text-slate-700">Financial Overview</h3>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} barCategoryGap="30%">
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={v => `₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={v => [`₹${v.toLocaleString('en-IN')}`, '']} />
              <Bar dataKey="value" radius={[4,4,0,0]}>
                {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Bot size={18} className="text-yellow-500" />
            <h3 className="font-semibold text-slate-700">AI Agent Activity</h3>
          </div>
          {agentStats ? (
            <div className="space-y-4">
              {[
                { label: 'Total Actions', value: agentStats.total_agent_actions, color: 'bg-blue-500' },
                { label: 'Tokens Consumed', value: (agentStats.total_tokens_used || 0).toLocaleString(), color: 'bg-purple-500' },
                { label: 'Success Rate', value: `${agentStats.success_rate}%`, color: 'bg-green-500' },
              ].map(s => (
                <div key={s.label} className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">{s.label}</span>
                  <span className={`badge text-white px-3 ${s.color}`}>{s.value}</span>
                </div>
              ))}
              <div className="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-400">
                Powered by Claude AI · All actions logged
              </div>
            </div>
          ) : <div className="animate-pulse space-y-3">{[...Array(3)].map((_,i)=><div key={i} className="h-8 bg-slate-100 rounded"/>)}</div>}
        </div>
      </div>
    </div>
  )
}
