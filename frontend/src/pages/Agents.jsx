import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Bot, CheckCircle, XCircle, Clock, Cpu } from 'lucide-react'

const agentInfo = {
  lead_scoring_agent:      { label: 'Lead Scoring',       module: 'CRM',      color: 'bg-blue-500' },
  pr_approval_agent:       { label: 'PR Approval',        module: 'Purchase',  color: 'bg-orange-500' },
  three_way_match_agent:   { label: '3-Way Match',        module: 'Purchase',  color: 'bg-purple-500' },
  mrp_planning_agent:      { label: 'MRP Planning',       module: 'Material',  color: 'bg-green-500' },
  payroll_audit_agent:     { label: 'Payroll Audit',      module: 'HR',        color: 'bg-pink-500' },
  financial_reporting_agent:{ label: 'Financial Insights', module: 'Finance',  color: 'bg-yellow-500' },
}

export default function Agents() {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState({})

  useEffect(()=>{
    api.get('/agents/logs').then(r=>setLogs(r.data)).catch(()=>{})
    api.get('/agents/stats').then(r=>setStats(r.data)).catch(()=>{})
  },[])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">AI Agent Control Centre</h1>
        <p className="text-slate-500 text-sm">Real-time view of all autonomous agent actions</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[{l:'Total Actions',v:stats.total_agent_actions||0},{l:'Tokens Used',v:(stats.total_tokens_used||0).toLocaleString()},{l:'Success Rate',v:`${stats.success_rate||0}%`}]
          .map(s=><div key={s.l} className="card p-4"><p className="text-xs text-slate-500">{s.l}</p><p className="text-2xl font-bold mt-1">{s.v}</p></div>)}
      </div>

      {/* Agent roster */}
      <div className="grid grid-cols-3 gap-4">
        {Object.entries(agentInfo).map(([key, info]) => (
          <div key={key} className="card p-4 flex items-center gap-3">
            <div className={`w-10 h-10 ${info.color} rounded-xl flex items-center justify-center shrink-0`}>
              <Bot size={20} className="text-white" />
            </div>
            <div>
              <p className="font-semibold text-sm">{info.label}</p>
              <p className="text-xs text-slate-400">{info.module} module</p>
              <span className="text-xs text-green-600 flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full inline-block"/> Active
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="card overflow-hidden">
        <div className="p-4 border-b font-semibold flex items-center gap-2"><Cpu size={16} className="text-purple-500"/>Agent Activity Log</div>
        <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>Agent</th><th>Module</th><th>Action</th><th>Tokens</th><th>Duration</th><th>Status</th><th>Time</th></tr></thead>
        <tbody>{logs.map(l=>{
          const info = agentInfo[l.agent_name] || {}
          return (
            <tr key={l.id}>
              <td><span className="font-medium text-xs">{info.label||l.agent_name}</span></td>
              <td><span className="badge-gray">{l.module}</span></td>
              <td className="text-slate-500 text-xs max-w-48 truncate">{l.action}</td>
              <td className="text-xs"><Cpu size={11} className="inline mr-1 text-purple-400"/>{l.tokens_used||0}</td>
              <td className="text-xs"><Clock size={11} className="inline mr-1 text-slate-400"/>{Math.round(l.duration_ms||0)}ms</td>
              <td>{l.success?<span className="badge-green flex items-center gap-1"><CheckCircle size={10}/>OK</span>:<span className="badge-red flex items-center gap-1"><XCircle size={10}/>Failed</span>}</td>
              <td className="text-xs text-slate-400">{new Date(l.created_at).toLocaleString('en-IN',{dateStyle:'short',timeStyle:'short'})}</td>
            </tr>
          )
        })}
        {!logs.length&&<tr><td colSpan={7} className="text-center text-slate-400 py-8">No agent actions yet — interact with the platform to see AI in action</td></tr>}
        </tbody></table></div>
      </div>
    </div>
  )
}
