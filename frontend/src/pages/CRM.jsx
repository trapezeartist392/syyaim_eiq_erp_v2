import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Plus, Star, TrendingUp, Pencil, X } from 'lucide-react'

const statusColor = { new:'badge-blue', contacted:'badge-yellow', qualified:'badge-yellow', proposal:'badge-blue', negotiation:'badge-yellow', won:'badge-green', lost:'badge-red' }
const STATUS_OPTIONS = ['new','contacted','qualified','proposal','negotiation','won','lost']
const CATEGORY_OPTIONS = ['raw_material','wip','finished_goods','consumables','spares']

const emptyForm = { company_name:'', contact_name:'', email:'', phone:'', source:'', value:0, gstin:'', item_name:'', item_code:'', item_category:'raw_material' }

export default function CRM() {
  const [leads, setLeads] = useState([])
  const [stats, setStats] = useState({})
  const [showForm, setShowForm] = useState(false)
  const [editLead, setEditLead] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(false)

  const load = () => {
    api.get('/crm/leads').then(r => setLeads(r.data)).catch(()=>{})
    api.get('/crm/stats').then(r => setStats(r.data)).catch(()=>{})
  }
  useEffect(() => { load() }, [])

  const openAdd = () => { setEditLead(null); setForm(emptyForm); setShowForm(true) }
  const openEdit = (l) => {
    setEditLead(l)
    setForm({
      company_name: l.company_name||'', contact_name: l.contact_name||'',
      email: l.email||'', phone: l.phone||'', source: l.source||'',
      value: l.value||0, status: l.status||'new',
      gstin: l.gstin||'', item_name: l.item_name||'',
      item_code: l.item_code||'', item_category: l.item_category||'raw_material'
    })
    setShowForm(true)
  }
  const closeForm = () => { setShowForm(false); setEditLead(null); setForm(emptyForm) }

  const submit = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      if (editLead) {
        await api.put(`/crm/leads/${editLead.id}`, form)
      } else {
        await api.post('/crm/leads', form)
      }
      closeForm(); load()
    } finally { setLoading(false) }
  }

  const f = (k) => e => setForm({...form, [k]: e.target.value})
  const scoreColor = s => s >= 70 ? 'text-green-600' : s >= 40 ? 'text-yellow-600' : 'text-red-500'

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">CRM & Sales</h1>
          <p className="text-slate-500 text-sm">Lead management with AI scoring</p>
        </div>
        <button className="btn-primary" onClick={openAdd}><Plus size={16}/>Add Lead</button>
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

      {/* Add / Edit Lead Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-800">{editLead ? 'Edit Lead' : 'Add Lead'}</h3>
              <button onClick={closeForm} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <form onSubmit={submit} className="space-y-3">

              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Company Info</p>
              <div>
                <label className="label">Company Name *</label>
                <input className="input" value={form.company_name} onChange={f('company_name')} required/>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">GSTIN</label>
                  <input className="input" placeholder="22AAAAA0000A1Z5" value={form.gstin} onChange={f('gstin')} maxLength={15}/>
                </div>
                <div>
                  <label className="label">Lead Source</label>
                  <input className="input" placeholder="LinkedIn, Referral..." value={form.source} onChange={f('source')}/>
                </div>
              </div>

              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mt-2">Contact Info</p>
              <div>
                <label className="label">Contact Name</label>
                <input className="input" value={form.contact_name} onChange={f('contact_name')}/>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Email</label>
                  <input className="input" type="email" value={form.email} onChange={f('email')}/>
                </div>
                <div>
                  <label className="label">Phone</label>
                  <input className="input" value={form.phone} onChange={f('phone')}/>
                </div>
              </div>

              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mt-2">Item / Product Info</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Item Code</label>
                  <input className="input" placeholder="e.g. RM-001" value={form.item_code} onChange={f('item_code')}/>
                </div>
                <div>
                  <label className="label">Item Name</label>
                  <input className="input" placeholder="e.g. Steel Rods" value={form.item_name} onChange={f('item_name')}/>
                </div>
              </div>
              <div>
                <label className="label">Category</label>
                <select className="input" value={form.item_category} onChange={f('item_category')}>
                  {CATEGORY_OPTIONS.map(c => (
                    <option key={c} value={c}>{c.replace(/_/g,' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                  ))}
                </select>
              </div>

              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mt-2">Deal Info</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Estimated Value (₹)</label>
                  <input className="input" type="number" value={form.value} onChange={e=>setForm({...form,value:+e.target.value})}/>
                </div>
                {editLead && (
                  <div>
                    <label className="label">Status</label>
                    <select className="input" value={form.status} onChange={f('status')}>
                      {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
                    </select>
                  </div>
                )}
              </div>

              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={loading} className="btn-primary flex-1">
                  {loading ? 'Saving...' : editLead ? 'Update Lead' : 'Add Lead + AI Score'}
                </button>
                <button type="button" className="btn-outline" onClick={closeForm}>Cancel</button>
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
              <th>Company</th><th>GSTIN</th><th>Contact</th><th>Item</th><th>Category</th>
              <th>Status</th><th>AI Score</th><th>Value</th><th>Notes</th><th>Edit</th>
            </tr></thead>
            <tbody>
              {leads.map(l => (
                <tr key={l.id}>
                  <td className="font-medium">{l.company_name}</td>
                  <td className="text-slate-500 text-xs">{l.gstin||'—'}</td>
                  <td className="text-slate-500">{l.contact_name||'—'}</td>
                  <td className="text-slate-500">{l.item_code ? `${l.item_code} · ${l.item_name}` : l.item_name||'—'}</td>
                  <td className="text-slate-500 text-xs">{l.item_category ? l.item_category.replace(/_/g,' ') : '—'}</td>
                  <td><span className={statusColor[l.status]||'badge-gray'}>{l.status}</span></td>
                  <td>
                    <span className={`font-bold ${scoreColor(l.ai_score)}`}>
                      <Star size={12} className="inline mr-1"/>{l.ai_score}
                    </span>
                  </td>
                  <td>₹{(l.value||0).toLocaleString('en-IN')}</td>
                  <td className="text-slate-400 text-xs max-w-40 truncate">{l.ai_notes||'—'}</td>
                  <td>
                    <button onClick={() => openEdit(l)} className="text-blue-500 hover:text-blue-700">
                      <Pencil size={14}/>
                    </button>
                  </td>
                </tr>
              ))}
              {!leads.length && <tr><td colSpan={10} className="text-center text-slate-400 py-8">No leads yet — add your first lead</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
