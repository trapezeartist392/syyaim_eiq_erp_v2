import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Plus, Package, AlertTriangle, Zap } from 'lucide-react'

export default function Material() {
  const [items, setItems] = useState([])
  const [stats, setStats] = useState({})
  const [mrpResult, setMrpResult] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [mrpLoading, setMrpLoading] = useState(false)
  const [form, setForm] = useState({ code:'', name:'', category:'raw_material', unit:'pcs', current_stock:0, reorder_point:0, reorder_qty:0, unit_cost:0 })

  const load = () => {
    api.get('/material/items').then(r=>setItems(r.data)).catch(()=>{})
    api.get('/material/stats').then(r=>setStats(r.data)).catch(()=>{})
  }
  useEffect(()=>{ load() },[])

  const submit = async (e) => {
    e.preventDefault(); setLoading(true)
    try { await api.post('/material/items', {...form,current_stock:+form.current_stock,reorder_point:+form.reorder_point,reorder_qty:+form.reorder_qty,unit_cost:+form.unit_cost}); setShowForm(false); load() }
    finally { setLoading(false) }
  }

  const runMRP = async () => {
    setMrpLoading(true)
    try { const r = await api.get('/material/mrp-plan'); setMrpResult(r.data) }
    finally { setMrpLoading(false) }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-800">Material Management</h1>
        <p className="text-slate-500 text-sm">Inventory control with AI-powered MRP</p></div>
        <div className="flex gap-2">
          <button className="btn-gold" onClick={runMRP} disabled={mrpLoading}><Zap size={16}/>{mrpLoading?'Planning...':'Run AI MRP'}</button>
          <button className="btn-primary" onClick={()=>setShowForm(true)}><Plus size={16}/>Add Item</button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[{l:'Total Items',v:stats.total_items||0},{l:'Low Stock Alerts',v:stats.low_stock_items||0,alert:true},{l:'Inventory Value',v:`₹${((stats.inventory_value||0)/100000).toFixed(1)}L`}]
          .map(s=><div key={s.l} className="card p-4">{s.alert&&<AlertTriangle size={14} className="text-red-500 mb-1"/>}<p className="text-xs text-slate-500">{s.l}</p><p className={`text-2xl font-bold mt-1 ${s.alert&&s.v>0?'text-red-600':''}`}>{s.v}</p></div>)}
      </div>

      {mrpResult && (
        <div className="card p-5 border-yellow-300 bg-yellow-50">
          <div className="flex items-center gap-2 mb-3 font-semibold text-yellow-800"><Zap size={16}/>AI MRP Recommendations</div>
          <p className="text-sm text-yellow-700 mb-3">{mrpResult.data?.summary || mrpResult.raw?.slice(0,200)}</p>
          {mrpResult.data?.recommendations?.map((r,i)=>(
            <div key={i} className="bg-white rounded-lg p-3 mb-2 text-sm">
              <span className="font-medium">{r.item_name}</span> — Order <span className="font-bold text-blue-700">{r.recommended_order_qty} units</span>
              <span className={`ml-2 badge ${r.urgency==='critical'?'badge-red':r.urgency==='high'?'badge-yellow':'badge-blue'}`}>{r.urgency}</span>
              <p className="text-slate-500 text-xs mt-1">{r.reason}</p>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6">
            <h3 className="font-bold mb-4">Add Inventory Item</h3>
            <form onSubmit={submit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="label">Item Code</label><input className="input" value={form.code} onChange={e=>setForm({...form,code:e.target.value})} required/></div>
                <div><label className="label">Unit</label><input className="input" value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}/></div>
              </div>
              <div><label className="label">Item Name</label><input className="input" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/></div>
              <div><label className="label">Category</label>
                <select className="input" value={form.category} onChange={e=>setForm({...form,category:e.target.value})}>
                  {['raw_material','wip','finished_goods','consumables','spares'].map(c=><option key={c} value={c}>{c.replace(/_/g,' ')}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[['current_stock','Current Stock'],['reorder_point','Reorder Point'],['reorder_qty','Reorder Qty'],['unit_cost','Unit Cost (₹)']].map(([k,l])=>(
                  <div key={k}><label className="label">{l}</label><input className="input" type="number" value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})}/></div>
                ))}
              </div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={loading} className="btn-primary flex-1">{loading?'Saving...':'Add Item'}</button>
                <button type="button" className="btn-outline" onClick={()=>setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card overflow-hidden">
        <div className="p-4 border-b font-semibold flex items-center gap-2"><Package size={16} className="text-green-500"/>Inventory</div>
        <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>Code</th><th>Name</th><th>Category</th><th>Stock</th><th>Reorder Pt.</th><th>Unit Cost</th><th>Status</th></tr></thead>
        <tbody>{items.map(i=>(
          <tr key={i.id}>
            <td className="font-mono text-xs">{i.code}</td>
            <td className="font-medium">{i.name}</td>
            <td><span className="badge-gray">{i.category.replace(/_/g,' ')}</span></td>
            <td className={i.below_reorder?'font-bold text-red-600':''}>{i.current_stock} {i.unit}</td>
            <td className="text-slate-400">{i.reorder_point}</td>
            <td>₹{i.unit_cost.toLocaleString('en-IN')}</td>
            <td>{i.below_reorder?<span className="badge-red">Low Stock</span>:<span className="badge-green">OK</span>}</td>
          </tr>
        ))}
        {!items.length&&<tr><td colSpan={7} className="text-center text-slate-400 py-8">No items yet</td></tr>}
        </tbody></table></div>
      </div>
    </div>
  )
}
