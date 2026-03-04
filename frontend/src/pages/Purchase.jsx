import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Plus, ShoppingCart, CheckCircle } from 'lucide-react'

export default function Purchase() {
  const [prs, setPRs] = useState([])
  const [pos, setPOs] = useState([])
  const [stats, setStats] = useState({})
  const [showPRForm, setShowPRForm] = useState(false)
  const [form, setForm] = useState({ item_description:'', quantity:1, unit:'pcs', estimated_cost:'', department:'' })
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('pr')

  const load = () => {
    api.get('/purchase/requisitions').then(r=>setPRs(r.data)).catch(()=>{})
    api.get('/purchase/orders').then(r=>setPOs(r.data)).catch(()=>{})
    api.get('/purchase/stats').then(r=>setStats(r.data)).catch(()=>{})
  }
  useEffect(()=>{ load() },[])

  const submitPR = async (e) => {
    e.preventDefault(); setLoading(true)
    try { await api.post('/purchase/requisitions',{...form,quantity:+form.quantity,estimated_cost:+form.estimated_cost||null}); setShowPRForm(false); load() }
    finally { setLoading(false) }
  }
  const approvePR = async (id) => { await api.patch(`/purchase/requisitions/${id}/approve`); load() }

  const statusColor = s => ({draft:'badge-gray',pending_approval:'badge-yellow',approved:'badge-green',rejected:'badge-red',po_created:'badge-blue'}[s]||'badge-gray')

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-800">Purchase</h1>
        <p className="text-slate-500 text-sm">Requisitions and orders with AI review</p></div>
        <button className="btn-primary" onClick={()=>setShowPRForm(true)}><Plus size={16}/>New PR</button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[{l:'Total PRs',v:stats.total_prs||0},{l:'Pending Approval',v:stats.pending_approval||0},{l:'Total POs',v:stats.total_pos||0},{l:'PO Value',v:`₹${((stats.total_po_value||0)/100000).toFixed(1)}L`}]
          .map(s=><div key={s.l} className="card p-4"><p className="text-xs text-slate-500">{s.l}</p><p className="text-2xl font-bold mt-1">{s.v}</p></div>)}
      </div>

      {showPRForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6">
            <h3 className="font-bold mb-4">Create Purchase Requisition</h3>
            <form onSubmit={submitPR} className="space-y-3">
              <div><label className="label">Item Description</label><textarea className="input" rows={2} value={form.item_description} onChange={e=>setForm({...form,item_description:e.target.value})} required/></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="label">Quantity</label><input className="input" type="number" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})} required/></div>
                <div><label className="label">Unit</label><input className="input" value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}/></div>
              </div>
              <div><label className="label">Estimated Cost (₹)</label><input className="input" type="number" value={form.estimated_cost} onChange={e=>setForm({...form,estimated_cost:e.target.value})}/></div>
              <div><label className="label">Department</label><input className="input" value={form.department} onChange={e=>setForm({...form,department:e.target.value})}/></div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={loading} className="btn-primary flex-1">{loading?'AI Reviewing...':'Submit PR + AI Review'}</button>
                <button type="button" className="btn-outline" onClick={()=>setShowPRForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {['pr','po'].map(t=><button key={t} onClick={()=>setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-medium ${tab===t?'bg-blue-700 text-white':'btn-outline'}`}>{t==='pr'?'Purchase Requisitions':'Purchase Orders'}</button>)}
      </div>

      <div className="card overflow-hidden">
        {tab==='pr' ? (
          <><div className="p-4 border-b font-semibold flex items-center gap-2"><ShoppingCart size={16} className="text-orange-500"/>Purchase Requisitions</div>
          <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>PR #</th><th>Description</th><th>Qty</th><th>Est. Cost</th><th>Status</th><th>AI Recommendation</th><th>Action</th></tr></thead>
          <tbody>{prs.map(p=>(
            <tr key={p.id}>
              <td className="font-mono text-xs">{p.pr_number}</td>
              <td className="max-w-xs truncate">{p.item_description}</td>
              <td>{p.quantity}</td>
              <td>{p.estimated_cost ? `₹${p.estimated_cost.toLocaleString('en-IN')}` : '—'}</td>
              <td><span className={statusColor(p.status)}>{p.status}</span></td>
              <td className="text-xs text-slate-400 max-w-48 truncate">{p.ai_recommendation||'—'}</td>
              <td>{p.status==='pending_approval'&&<button onClick={()=>approvePR(p.id)} className="badge-green cursor-pointer hover:bg-green-200 flex items-center gap-1"><CheckCircle size={11}/>Approve</button>}</td>
            </tr>
          ))}
          {!prs.length&&<tr><td colSpan={7} className="text-center text-slate-400 py-8">No requisitions yet</td></tr>}
          </tbody></table></div></>
        ) : (
          <><div className="p-4 border-b font-semibold flex items-center gap-2"><ShoppingCart size={16} className="text-blue-500"/>Purchase Orders</div>
          <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>PO #</th><th>Vendor</th><th>Amount</th><th>Status</th><th>3-Way Match</th></tr></thead>
          <tbody>{pos.map(p=>(
            <tr key={p.id}>
              <td className="font-mono text-xs">{p.po_number}</td>
              <td>{p.vendor_id}</td>
              <td>₹{(p.total_amount||0).toLocaleString('en-IN')}</td>
              <td><span className={statusColor(p.status)}>{p.status}</span></td>
              <td><span className="badge-gray">{p.three_way_match_status}</span></td>
            </tr>
          ))}
          {!pos.length&&<tr><td colSpan={5} className="text-center text-slate-400 py-8">No purchase orders yet</td></tr>}
          </tbody></table></div></>
        )}
      </div>
    </div>
  )
}
