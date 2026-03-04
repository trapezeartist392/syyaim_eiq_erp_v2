import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Plus, Star, TrendingUp } from 'lucide-react'

const statusColor = { new:'badge-blue', contacted:'badge-yellow', qualified:'badge-yellow', proposal:'badge-blue', negotiation:'badge-yellow', won:'badge-green', lost:'badge-red' }

export default function CRM() {
  const [leads, setLeads] = useState([])
  const [stats, setStats] = useState({})
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ company_name:'', contact_name:'', email:'', phone:'', source:'', value:0 })
  const [loading, setLoading] = useState(false)

  const load = () => {
    api.get('/crm/leads').then(r => setLeads(r.data)).catch(()=>{})
    api.get('/crm/stats').then(r => setStats(r.data)).catch(()=>{})
  }
  useEffect(() => { load() }, [])

  const submit = async (e) => {
    e.preventDefault(); setLoading(true)
    try { await api.post('/crm/leads', form); setShowForm(false); setForm({ company_name:'', contact_name:'', email:'', phone:'', source:'', value:0 }); load() }
    finally { setLoading(false) }
  }

  const scoreColor = s => s >= 70 ? 'text-green-600' : s >= 40 ? 'text-yellow-600' : 'text-red-500'

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">CRM & Sales</h1>
          <p className="text-slate-500 text-sm">Lead management with AI scoring</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(true)}><Plus size={16}/>Add Lead</button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          {label:'Total Leads', value: stats.total_leads||0},
          {label:'Won', value: stats.won_leads||0},
          {label:'Pipeline Value', value: `₹${((stats.pipeline_value||0)/100000).toFixed(1)}L`},
          {label:'Orders', value: stats.total_orders||0},
        ].map(s => (
          <div key={s.label} className="card p-4">
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Add Lead Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6">
            <h3 className="font-bold text-slate-800 mb-4">Add Lead</h3>
            <form onSubmit={submit} className="space-y-3">
              {[['company_name','Company Name',true],['contact_name','Contact Name'],['email','Email'],['phone','Phone'],['source','Lead Source']].map(([k,l,req])=>(
                <div key={k}><label className="label">{l}</label>
                <input className="input" value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})} required={!!req}/></div>
              ))}
              <div><label className="label">Estimated Value (₹)</label>
              <input className="input" type="number" value={form.value} onChange={e=>setForm({...form,value:+e.target.value})}/></div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={loading} className="btn-primary flex-1">{loading?'Saving & Scoring...':'Add Lead + AI Score'}</button>
                <button type="button" className="btn-outline" onClick={()=>setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Leads Table */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b border-slate-100 font-semibold text-slate-700 flex items-center gap-2">
          <TrendingUp size={16} className="text-blue-500" /> Leads Pipeline
        </div>
        <div className="overflow-x-auto">
          <table className="miq-table">
            <thead><tr>
              <th>Company</th><th>Contact</th><th>Status</th>
              <th>AI Score</th><th>Value</th><th>Notes</th>
            </tr></thead>
            <tbody>
              {leads.map(l => (
                <tr key={l.id}>
                  <td className="font-medium">{l.company_name}</td>
                  <td className="text-slate-500">{l.contact_name || '—'}</td>
                  <td><span className={statusColor[l.status]||'badge-gray'}>{l.status}</span></td>
                  <td>
                    <span className={`font-bold ${scoreColor(l.ai_score)}`}>
                      <Star size={12} className="inline mr-1"/>{l.ai_score}
                    </span>
                  </td>
                  <td>₹{(l.value||0).toLocaleString('en-IN')}</td>
                  <td className="text-slate-400 text-xs max-w-48 truncate">{l.ai_notes||'—'}</td>
                </tr>
              ))}
              {!leads.length && <tr><td colSpan={6} className="text-center text-slate-400 py-8">No leads yet — add your first lead</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
