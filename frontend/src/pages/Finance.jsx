import { useEffect, useState } from 'react'
import api from '../utils/api'
import { DollarSign, Zap, TrendingUp, TrendingDown } from 'lucide-react'

export default function Finance() {
  const [accounts, setAccounts] = useState([])
  const [pl, setPL] = useState(null)
  const [insights, setInsights] = useState(null)
  const [insightsLoading, setInsightsLoading] = useState(false)

  const load = () => {
    api.get('/finance/accounts').then(r=>setAccounts(r.data)).catch(()=>{})
    api.get('/finance/pl-summary').then(r=>setPL(r.data)).catch(()=>{})
  }
  useEffect(()=>{ load() },[])

  const getInsights = async () => {
    setInsightsLoading(true)
    try { const r = await api.get('/finance/ai-insights'); setInsights(r.data) }
    finally { setInsightsLoading(false) }
  }

  const fmt = n => `₹${(n||0).toLocaleString('en-IN')}`
  const typeColor = t => ({asset:'badge-blue',liability:'badge-red',equity:'badge-gray',income:'badge-green',expense:'badge-yellow'}[t]||'badge-gray')

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-800">Finance & Accounting</h1>
        <p className="text-slate-500 text-sm">Chart of accounts with AI financial insights</p></div>
        <button className="btn-gold" onClick={getInsights} disabled={insightsLoading}><Zap size={16}/>{insightsLoading?'Analysing...':'AI Insights'}</button>
      </div>

      {pl && (
        <div className="grid grid-cols-4 gap-4">
          {[
            {l:'Total Income',v:fmt(pl.total_income),icon:TrendingUp,color:'text-green-600'},
            {l:'Total Expense',v:fmt(pl.total_expense),icon:TrendingDown,color:'text-red-600'},
            {l:'Net Profit',v:fmt(pl.net_profit),icon:DollarSign,color:pl.net_profit>=0?'text-green-600':'text-red-600'},
            {l:'Total Assets',v:fmt(pl.total_assets),icon:DollarSign,color:'text-blue-600'},
          ].map(s=>(
            <div key={s.l} className="card p-4 flex items-start gap-3">
              <s.icon size={20} className={`${s.color} mt-1 shrink-0`}/>
              <div><p className="text-xs text-slate-500">{s.l}</p><p className={`text-xl font-bold mt-0.5 ${s.color}`}>{s.v}</p></div>
            </div>
          ))}
        </div>
      )}

      {insights && (
        <div className="card p-5 bg-blue-50 border-blue-200">
          <div className="flex items-center gap-2 mb-3 font-semibold text-blue-800"><Zap size={16}/>AI Financial Insights</div>
          {insights.success ? (
            <div className="space-y-3">
              <p className="text-sm text-slate-700">{insights.data?.summary || insights.raw?.slice(0,300)}</p>
              {insights.data?.key_insights?.map((k,i)=><p key={i} className="text-sm text-blue-700">• {k}</p>)}
              {insights.data?.recommendations?.length>0 && (
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <p className="text-xs font-semibold text-blue-800 mb-1">RECOMMENDATIONS</p>
                  {insights.data.recommendations.map((r,i)=><p key={i} className="text-sm text-slate-600">→ {r}</p>)}
                </div>
              )}
            </div>
          ) : <p className="text-sm text-red-600">{insights.error}</p>}
        </div>
      )}

      <div className="card overflow-hidden">
        <div className="p-4 border-b font-semibold flex items-center gap-2"><DollarSign size={16} className="text-green-500"/>Chart of Accounts</div>
        <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>Code</th><th>Account Name</th><th>Type</th><th>Balance</th></tr></thead>
        <tbody>{accounts.map(a=>(
          <tr key={a.id}>
            <td className="font-mono text-xs">{a.code}</td>
            <td className="font-medium">{a.name}</td>
            <td><span className={typeColor(a.account_type)}>{a.account_type}</span></td>
            <td className="font-medium">{fmt(a.balance)}</td>
          </tr>
        ))}
        {!accounts.length&&<tr><td colSpan={4} className="text-center text-slate-400 py-8">No accounts configured</td></tr>}
        </tbody></table></div>
      </div>
    </div>
  )
}
