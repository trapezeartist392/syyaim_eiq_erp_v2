import { useState } from 'react'
import api from '../utils/api'
import { CheckCircle, Circle, ChevronRight, ChevronLeft, Building2, Package, Users, BookOpen, Rocket } from 'lucide-react'

const STEPS = [
  { id: 'client',   label: 'Client',    icon: Building2, desc: 'Add your first lead / client' },
  { id: 'item',     label: 'Inventory', icon: Package,   desc: 'Add your first inventory item' },
  { id: 'employee', label: 'Employee',  icon: Users,     desc: 'Add your first employee' },
  { id: 'account',  label: 'Account GL',icon: BookOpen,  desc: 'Set up a GL account' },
]

const ITEM_CATEGORIES = ['raw_material','wip','finished_goods','consumables','spares']
const ACCOUNT_TYPES   = ['asset','liability','equity','income','expense']
const EMP_TYPES       = ['full_time','part_time','contract']

function StepIndicator({ steps, current, done }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {steps.map((s, i) => {
        const isDone    = done.includes(s.id)
        const isCurrent = current === i
        return (
          <div key={s.id} className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all
              ${isDone    ? 'bg-green-100 text-green-700' :
                isCurrent ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' :
                            'bg-slate-100 text-slate-400'}`}>
              {isDone ? <CheckCircle size={14}/> : <Circle size={14}/>}
              {s.label}
            </div>
            {i < steps.length - 1 && <ChevronRight size={14} className="text-slate-300"/>}
          </div>
        )
      })}
    </div>
  )
}

function StepActions({ loading, onSkip, label }) {
  return (
    <div className="flex gap-3 pt-2">
      <button type="submit" disabled={loading}
        className="flex-1 bg-blue-600 text-white py-2.5 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
        {loading ? 'Saving...' : <>{label} <ChevronRight size={16}/></>}
      </button>
      <button type="button" onClick={onSkip}
        className="px-4 py-2.5 text-slate-500 hover:text-slate-700 text-sm font-medium transition-colors">
        Skip
      </button>
    </div>
  )
}

function ClientStep({ onDone, onSkip }) {
  const [f, setF] = useState({ company_name:'', contact_name:'', email:'', phone:'', gstin:'', source:'', value:0 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try { await api.post('/crm/leads', f); onDone() }
    catch(err) { setError(err.response?.data?.detail || 'Failed to save client') }
    finally { setLoading(false) }
  }
  const fld = (k) => e => setF({...f,[k]:e.target.value})
  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="label">Company Name *</label>
          <input className="input" value={f.company_name} onChange={fld('company_name')} required placeholder="Acme Manufacturing Pvt Ltd"/>
        </div>
        <div><label className="label">GSTIN</label>
          <input className="input" value={f.gstin} onChange={fld('gstin')} maxLength={15} placeholder="22AAAAA0000A1Z5"/></div>
        <div><label className="label">Lead Source</label>
          <input className="input" value={f.source} onChange={fld('source')} placeholder="Referral, LinkedIn..."/></div>
        <div><label className="label">Contact Person</label>
          <input className="input" value={f.contact_name} onChange={fld('contact_name')} placeholder="Rajesh Kumar"/></div>
        <div><label className="label">Phone</label>
          <input className="input" value={f.phone} onChange={fld('phone')} placeholder="+91 98765 43210"/></div>
        <div><label className="label">Work Email</label>
          <input className="input" type="email" value={f.email} onChange={fld('email')} placeholder="rajesh@acme.com"/></div>
        <div><label className="label">Estimated Value (₹)</label>
          <input className="input" type="number" value={f.value} onChange={e=>setF({...f,value:+e.target.value})}/></div>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <StepActions loading={loading} onSkip={onSkip} label="Save Client & Continue"/>
    </form>
  )
}

function ItemStep({ onDone, onSkip }) {
  const [f, setF] = useState({ code:'', name:'', category:'raw_material', unit:'pcs', current_stock:0, reorder_point:0, reorder_qty:0, unit_cost:0 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try { await api.post('/material/items', f); onDone() }
    catch(err) { setError(err.response?.data?.detail || 'Failed to save item') }
    finally { setLoading(false) }
  }
  const fld = (k) => e => setF({...f,[k]:e.target.value})
  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div><label className="label">Item Code *</label>
          <input className="input" value={f.code} onChange={fld('code')} required placeholder="RM-001"/></div>
        <div><label className="label">Item Name *</label>
          <input className="input" value={f.name} onChange={fld('name')} required placeholder="Steel Rods"/></div>
        <div><label className="label">Category</label>
          <select className="input" value={f.category} onChange={fld('category')}>
            {ITEM_CATEGORIES.map(c=><option key={c} value={c}>{c.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</option>)}
          </select></div>
        <div><label className="label">Unit</label>
          <input className="input" value={f.unit} onChange={fld('unit')} placeholder="pcs, kg, ltr..."/></div>
        <div><label className="label">Current Stock</label>
          <input className="input" type="number" value={f.current_stock} onChange={e=>setF({...f,current_stock:+e.target.value})}/></div>
        <div><label className="label">Unit Cost (₹)</label>
          <input className="input" type="number" value={f.unit_cost} onChange={e=>setF({...f,unit_cost:+e.target.value})}/></div>
        <div><label className="label">Reorder Point</label>
          <input className="input" type="number" value={f.reorder_point} onChange={e=>setF({...f,reorder_point:+e.target.value})}/></div>
        <div><label className="label">Reorder Qty</label>
          <input className="input" type="number" value={f.reorder_qty} onChange={e=>setF({...f,reorder_qty:+e.target.value})}/></div>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <StepActions loading={loading} onSkip={onSkip} label="Save Item & Continue"/>
    </form>
  )
}

function EmployeeStep({ onDone, onSkip }) {
  const [f, setF] = useState({ full_name:'', email:'', phone:'', department:'', designation:'', employment_type:'full_time', basic_salary:0, date_of_joining: new Date().toISOString().split('T')[0] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try { await api.post('/hr/employees', f); onDone() }
    catch(err) { setError(err.response?.data?.detail || 'Failed to save employee') }
    finally { setLoading(false) }
  }
  const fld = (k) => e => setF({...f,[k]:e.target.value})
  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2"><label className="label">Full Name *</label>
          <input className="input" value={f.full_name} onChange={fld('full_name')} required placeholder="Amit Sharma"/></div>
        <div><label className="label">Work Email</label>
          <input className="input" type="email" value={f.email} onChange={fld('email')} placeholder="amit@company.com"/></div>
        <div><label className="label">Phone</label>
          <input className="input" value={f.phone} onChange={fld('phone')} placeholder="+91 98765 43210"/></div>
        <div><label className="label">Department</label>
          <input className="input" value={f.department} onChange={fld('department')} placeholder="Production, Sales..."/></div>
        <div><label className="label">Designation</label>
          <input className="input" value={f.designation} onChange={fld('designation')} placeholder="Manager, Engineer..."/></div>
        <div><label className="label">Employment Type</label>
          <select className="input" value={f.employment_type} onChange={fld('employment_type')}>
            {EMP_TYPES.map(t=><option key={t} value={t}>{t.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</option>)}
          </select></div>
        <div><label className="label">Date of Joining</label>
          <input className="input" type="date" value={f.date_of_joining} onChange={fld('date_of_joining')}/></div>
        <div className="col-span-2"><label className="label">Basic Salary (₹/month)</label>
          <input className="input" type="number" value={f.basic_salary} onChange={e=>setF({...f,basic_salary:+e.target.value})}/></div>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <StepActions loading={loading} onSkip={onSkip} label="Save Employee & Continue"/>
    </form>
  )
}

function AccountStep({ onDone, onSkip }) {
  const [f, setF] = useState({ code:'', name:'', account_type:'asset' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try { await api.post('/finance/accounts', f); onDone() }
    catch(err) { setError(err.response?.data?.detail || 'Failed to save account') }
    finally { setLoading(false) }
  }
  const fld = (k) => e => setF({...f,[k]:e.target.value})
  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div><label className="label">Account Code *</label>
          <input className="input" value={f.code} onChange={fld('code')} required placeholder="1001"/></div>
        <div><label className="label">Account Name *</label>
          <input className="input" value={f.name} onChange={fld('name')} required placeholder="Cash & Bank"/></div>
        <div className="col-span-2">
          <label className="label">Account Type</label>
          <div className="grid grid-cols-5 gap-2 mt-1">
            {ACCOUNT_TYPES.map(t=>(
              <button key={t} type="button" onClick={()=>setF({...f,account_type:t})}
                className={`py-2 px-3 rounded-lg text-sm font-medium border transition-all
                  ${f.account_type===t ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:border-blue-300'}`}>
                {t.charAt(0).toUpperCase()+t.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div className="col-span-2 bg-blue-50 rounded-lg p-3 text-sm text-blue-700">
          <strong>Tip:</strong> Start with Cash (Asset), Sales Revenue (Income), and Purchases (Expense).
        </div>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <StepActions loading={loading} onSkip={onSkip} label="Save Account & Finish"/>
    </form>
  )
}

function CompletionScreen({ done }) {
  return (
    <div className="text-center py-8">
      <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Rocket size={36} className="text-green-600"/>
      </div>
      <h2 className="text-2xl font-bold text-slate-800 mb-2">You're all set!</h2>
      <p className="text-slate-500 mb-6">Your ERP is configured and ready to use.</p>
      <div className="grid grid-cols-2 gap-3 max-w-xs mx-auto mb-8">
        {STEPS.map(s=>(
          <div key={s.id} className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm
            ${done.includes(s.id) ? 'bg-green-50 text-green-700' : 'bg-slate-50 text-slate-400'}`}>
            {done.includes(s.id) ? <CheckCircle size={14}/> : <Circle size={14}/>}
            {s.label}
          </div>
        ))}
      </div>
      <a href="/" className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors">
        Go to Dashboard <ChevronRight size={16}/>
      </a>
    </div>
  )
}

export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [done, setDone] = useState([])
  const finished = step >= STEPS.length

  const markDone = () => { setDone(d=>[...d,STEPS[step].id]); setStep(s=>s+1) }
  const skip = () => setStep(s=>s+1)

  const stepForms = [
    <ClientStep   key="client"   onDone={markDone} onSkip={skip}/>,
    <ItemStep     key="item"     onDone={markDone} onSkip={skip}/>,
    <EmployeeStep key="employee" onDone={markDone} onSkip={skip}/>,
    <AccountStep  key="account"  onDone={markDone} onSkip={skip}/>,
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-1.5 rounded-full text-sm font-medium mb-4">
            <Rocket size={14}/> Quick Setup Wizard
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Set up your ERP in minutes</h1>
          <p className="text-slate-500 mt-1">Add your first client, item, employee and account to get started</p>
        </div>

        {!finished && <StepIndicator steps={STEPS} current={step} done={done}/>}

        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
          {finished ? <CompletionScreen done={done}/> : (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                  {(() => { const Icon = STEPS[step].icon; return <Icon size={20} className="text-blue-600"/> })()}
                </div>
                <div>
                  <h2 className="font-bold text-slate-800">Step {step+1}: {STEPS[step].label}</h2>
                  <p className="text-slate-500 text-sm">{STEPS[step].desc}</p>
                </div>
                <div className="ml-auto text-sm text-slate-400">{step+1} / {STEPS.length}</div>
              </div>
              {stepForms[step]}
            </>
          )}
        </div>

        {!finished && step > 0 && (
          <button onClick={()=>setStep(s=>s-1)}
            className="flex items-center gap-1 text-slate-400 hover:text-slate-600 text-sm mt-4 mx-auto">
            <ChevronLeft size={14}/> Back
          </button>
        )}
      </div>
    </div>
  )
}
