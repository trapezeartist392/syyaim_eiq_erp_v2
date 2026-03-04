import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Plus, UserCog, AlertTriangle } from 'lucide-react'

export default function HR() {
  const [employees, setEmployees] = useState([])
  const [payrolls, setPayrolls] = useState([])
  const [stats, setStats] = useState({})
  const [tab, setTab] = useState('emp')
  const [showEmpForm, setShowEmpForm] = useState(false)
  const [showPayrollForm, setShowPayrollForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [empForm, setEmpForm] = useState({ employee_id:'', full_name:'', email:'', department:'', designation:'', basic_salary:0, hra:0, allowances:0 })
  const [payForm, setPayForm] = useState({ employee_id:'', month: new Date().getMonth()+1, year: new Date().getFullYear(), present_days:26 })

  const load = () => {
    api.get('/hr/employees').then(r=>setEmployees(r.data)).catch(()=>{})
    api.get('/hr/payroll').then(r=>setPayrolls(r.data)).catch(()=>{})
    api.get('/hr/stats').then(r=>setStats(r.data)).catch(()=>{})
  }
  useEffect(()=>{ load() },[])

  const submitEmp = async (e) => {
    e.preventDefault(); setLoading(true)
    try { await api.post('/hr/employees',{...empForm,basic_salary:+empForm.basic_salary,hra:+empForm.hra,allowances:+empForm.allowances}); setShowEmpForm(false); load() }
    finally { setLoading(false) }
  }
  const submitPayroll = async (e) => {
    e.preventDefault(); setLoading(true)
    try { await api.post('/hr/payroll/process',{...payForm,employee_id:+payForm.employee_id,present_days:+payForm.present_days}); setShowPayrollForm(false); load() }
    finally { setLoading(false) }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-800">HR & Payroll</h1>
        <p className="text-slate-500 text-sm">Employee management with AI payroll audit</p></div>
        <div className="flex gap-2">
          <button className="btn-outline" onClick={()=>setShowPayrollForm(true)}>Process Payroll</button>
          <button className="btn-primary" onClick={()=>setShowEmpForm(true)}><Plus size={16}/>Add Employee</button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[{l:'Employees',v:stats.total_employees||0},{l:'Payroll Disbursed',v:`₹${((stats.total_payroll_disbursed||0)/100000).toFixed(1)}L`},{l:'Anomalies Flagged',v:stats.payroll_anomalies||0,alert:true}]
          .map(s=><div key={s.l} className="card p-4">{s.alert&&s.v>0&&<AlertTriangle size={14} className="text-red-500 mb-1"/>}<p className="text-xs text-slate-500">{s.l}</p><p className={`text-2xl font-bold mt-1 ${s.alert&&s.v>0?'text-red-600':''}`}>{s.v}</p></div>)}
      </div>

      {showEmpForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-lg p-6">
            <h3 className="font-bold mb-4">Add Employee</h3>
            <form onSubmit={submitEmp} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                {[['employee_id','Employee ID',true],['full_name','Full Name',true],['email','Email',true],['department','Department',true],['designation','Designation'],['basic_salary','Basic Salary'],['hra','HRA'],['allowances','Allowances']].map(([k,l,req])=>(
                  <div key={k}><label className="label">{l}</label><input className="input" value={empForm[k]} onChange={e=>setEmpForm({...empForm,[k]:e.target.value})} required={!!req}/></div>
                ))}
              </div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={loading} className="btn-primary flex-1">{loading?'Saving...':'Add Employee'}</button>
                <button type="button" className="btn-outline" onClick={()=>setShowEmpForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPayrollForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6">
            <h3 className="font-bold mb-4">Process Payroll</h3>
            <form onSubmit={submitPayroll} className="space-y-3">
              <div><label className="label">Employee</label>
                <select className="input" value={payForm.employee_id} onChange={e=>setPayForm({...payForm,employee_id:e.target.value})} required>
                  <option value="">Select employee...</option>
                  {employees.map(e=><option key={e.id} value={e.id}>{e.full_name} ({e.employee_id})</option>)}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div><label className="label">Month</label><input className="input" type="number" min="1" max="12" value={payForm.month} onChange={e=>setPayForm({...payForm,month:e.target.value})}/></div>
                <div><label className="label">Year</label><input className="input" type="number" value={payForm.year} onChange={e=>setPayForm({...payForm,year:e.target.value})}/></div>
                <div><label className="label">Days Present</label><input className="input" type="number" value={payForm.present_days} onChange={e=>setPayForm({...payForm,present_days:e.target.value})}/></div>
              </div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={loading} className="btn-primary flex-1">{loading?'Processing + AI Audit...':'Process + AI Audit'}</button>
                <button type="button" className="btn-outline" onClick={()=>setShowPayrollForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {[['emp','Employees'],['pay','Payroll']].map(([t,l])=><button key={t} onClick={()=>setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-medium ${tab===t?'bg-blue-700 text-white':'btn-outline'}`}>{l}</button>)}
      </div>

      <div className="card overflow-hidden">
        {tab==='emp' ? (
          <><div className="p-4 border-b font-semibold flex items-center gap-2"><UserCog size={16}/>Employees</div>
          <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Designation</th><th>Basic Salary</th></tr></thead>
          <tbody>{employees.map(e=>(
            <tr key={e.id}><td className="font-mono text-xs">{e.employee_id}</td><td className="font-medium">{e.full_name}</td><td>{e.department}</td><td>{e.designation}</td><td>₹{(e.basic_salary||0).toLocaleString('en-IN')}</td></tr>
          ))}
          {!employees.length&&<tr><td colSpan={5} className="text-center text-slate-400 py-8">No employees yet</td></tr>}
          </tbody></table></div></>
        ) : (
          <><div className="p-4 border-b font-semibold flex items-center gap-2"><UserCog size={16}/>Payroll Records</div>
          <div className="overflow-x-auto"><table className="miq-table"><thead><tr><th>Emp ID</th><th>Period</th><th>Gross</th><th>Net</th><th>Status</th><th>AI Flag</th></tr></thead>
          <tbody>{payrolls.map(p=>(
            <tr key={p.id}><td>{p.employee_id}</td><td>{p.month}/{p.year}</td><td>₹{(p.gross_salary||0).toLocaleString('en-IN')}</td><td className="font-bold">₹{(p.net_salary||0).toLocaleString('en-IN')}</td>
            <td><span className="badge-green">{p.status}</span></td>
            <td>{p.ai_anomaly_flag?<span className="badge-red flex items-center gap-1"><AlertTriangle size={10}/>Anomaly</span>:<span className="badge-green">Clear</span>}</td>
            </tr>
          ))}
          {!payrolls.length&&<tr><td colSpan={6} className="text-center text-slate-400 py-8">No payroll records yet</td></tr>}
          </tbody></table></div></>
        )}
      </div>
    </div>
  )
}
