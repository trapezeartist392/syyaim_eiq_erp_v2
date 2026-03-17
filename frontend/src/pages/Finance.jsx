// frontend/src/pages/Finance.jsx
// GL Accounts + Journal Entries + Summary Dashboard

import { useState, useEffect } from 'react'
import api from '../utils/api'
import {
  BookOpen, TrendingUp, TrendingDown, Scale, Plus,
  Search, Filter, ChevronRight, X, CheckCircle
} from 'lucide-react'

const TYPE_COLORS = {
  asset:     { bg:'#E6F1FB', text:'#185FA5', border:'#B5D4F4', dot:'#378ADD' },
  liability: { bg:'#FCEBEB', text:'#A32D2D', border:'#F7C1C1', dot:'#E24B4A' },
  equity:    { bg:'#EEEDFE', text:'#534AB7', border:'#CECBF6', dot:'#7F77DD' },
  income:    { bg:'#EAF3DE', text:'#3B6D11', border:'#C0DD97', dot:'#639922' },
  expense:   { bg:'#FAEEDA', text:'#854F0B', border:'#FAC775', dot:'#BA7517' },
}

const ACCOUNT_TYPES = ['asset','liability','equity','income','expense']

function TypeBadge({ type }) {
  const c = TYPE_COLORS[type] || TYPE_COLORS.asset
  return (
    <span style={{
      fontSize:11, padding:'2px 8px', borderRadius:4, fontWeight:500,
      background:c.bg, color:c.text, border:`0.5px solid ${c.border}`
    }}>{type}</span>
  )
}

function StatCard({ label, value, color, icon: Icon }) {
  return (
    <div style={{
      background:'#fff', borderRadius:12, padding:'16px 20px',
      border:'1px solid #e2e8f0', boxShadow:'0 1px 3px rgba(0,0,0,0.06)'
    }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
        <span style={{ fontSize:13, color:'#64748b' }}>{label}</span>
        <Icon size={18} color={color}/>
      </div>
      <div style={{ fontSize:24, fontWeight:700, color }}>{value}</div>
    </div>
  )
}

function NewAccountModal({ onClose, onSaved }) {
  const [f, setF] = useState({ code:'', name:'', account_type:'asset' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try {
      await api.post('/finance/accounts', f)
      onSaved()
    } catch(err) { setError(err.response?.data?.detail || 'Failed to create account') }
    finally { setLoading(false) }
  }

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', zIndex:1000, display:'flex', alignItems:'center', justifyContent:'center', padding:16 }}>
      <div style={{ background:'#fff', borderRadius:16, padding:24, width:'100%', maxWidth:440 }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20 }}>
          <h2 style={{ fontSize:18, fontWeight:700, color:'#0f172a' }}>New GL Account</h2>
          <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', color:'#94a3b8' }}><X size={20}/></button>
        </div>
        <form onSubmit={submit}>
          <div style={{ marginBottom:14 }}>
            <label style={{ fontSize:12, color:'#64748b', display:'block', marginBottom:4 }}>Account Code *</label>
            <input required value={f.code} onChange={e=>setF({...f,code:e.target.value})}
              placeholder="e.g. 1006, 5506"
              style={{ width:'100%', border:'1px solid #e2e8f0', borderRadius:8, padding:'9px 12px', fontSize:14 }}/>
            <div style={{ fontSize:11, color:'#94a3b8', marginTop:3 }}>1xxx=Asset · 2xxx=Liability · 3xxx=Equity · 4xxx=Income · 5xxx=Expense</div>
          </div>
          <div style={{ marginBottom:14 }}>
            <label style={{ fontSize:12, color:'#64748b', display:'block', marginBottom:4 }}>Account Name *</label>
            <input required value={f.name} onChange={e=>setF({...f,name:e.target.value})}
              placeholder="e.g. Cash in Hand"
              style={{ width:'100%', border:'1px solid #e2e8f0', borderRadius:8, padding:'9px 12px', fontSize:14 }}/>
          </div>
          <div style={{ marginBottom:20 }}>
            <label style={{ fontSize:12, color:'#64748b', display:'block', marginBottom:6 }}>Account Type *</label>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:6 }}>
              {ACCOUNT_TYPES.map(t => {
                const c = TYPE_COLORS[t]
                return (
                  <button key={t} type="button" onClick={()=>setF({...f,account_type:t})}
                    style={{
                      padding:'7px 4px', borderRadius:8, fontSize:11, fontWeight:600, cursor:'pointer',
                      border: f.account_type===t ? `1.5px solid ${c.dot}` : '1px solid #e2e8f0',
                      background: f.account_type===t ? c.bg : '#fff',
                      color: f.account_type===t ? c.text : '#64748b'
                    }}>{t}</button>
                )
              })}
            </div>
          </div>
          {error && <p style={{ color:'#ef4444', fontSize:12, marginBottom:10 }}>{error}</p>}
          <div style={{ display:'flex', gap:8 }}>
            <button type="submit" disabled={loading}
              style={{ flex:1, background:'#1e40af', color:'#fff', border:'none', borderRadius:8, padding:'10px', fontWeight:600, cursor:'pointer', fontSize:14 }}>
              {loading ? 'Creating...' : 'Create Account'}
            </button>
            <button type="button" onClick={onClose}
              style={{ padding:'10px 16px', border:'1px solid #e2e8f0', borderRadius:8, cursor:'pointer', fontSize:14 }}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function NewJournalModal({ accounts, onClose, onSaved }) {
  const [f, setF] = useState({ description:'', lines:[
    { account_id:'', type:'debit',  amount:0 },
    { account_id:'', type:'credit', amount:0 },
  ]})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const addLine = () => setF({...f, lines:[...f.lines, { account_id:'', type:'debit', amount:0 }]})
  const updateLine = (i, k, v) => {
    const lines = [...f.lines]; lines[i] = {...lines[i],[k]:v}; setF({...f,lines})
  }
  const removeLine = (i) => setF({...f, lines: f.lines.filter((_,idx)=>idx!==i)})

  const totalDebit  = f.lines.filter(l=>l.type==='debit').reduce((s,l)=>s+(+l.amount),0)
  const totalCredit = f.lines.filter(l=>l.type==='credit').reduce((s,l)=>s+(+l.amount),0)
  const balanced    = Math.abs(totalDebit - totalCredit) < 0.01

  const submit = async (e) => {
    e.preventDefault()
    if(!balanced) { setError('Debit and credit totals must be equal'); return }
    setLoading(true); setError('')
    try {
      await api.post('/finance/journals', {
        description: f.description,
        total_amount: totalDebit,
        lines: f.lines.map(l=>({ account_id:+l.account_id, debit: l.type==='debit'?+l.amount:0, credit: l.type==='credit'?+l.amount:0 }))
      })
      onSaved()
    } catch(err) { setError(err.response?.data?.detail || 'Failed to create journal') }
    finally { setLoading(false) }
  }

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', zIndex:1000, display:'flex', alignItems:'center', justifyContent:'center', padding:16 }}>
      <div style={{ background:'#fff', borderRadius:16, padding:24, width:'100%', maxWidth:600, maxHeight:'90vh', overflowY:'auto' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20 }}>
          <h2 style={{ fontSize:18, fontWeight:700 }}>New Journal Entry</h2>
          <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', color:'#94a3b8' }}><X size={20}/></button>
        </div>
        <form onSubmit={submit}>
          <div style={{ marginBottom:14 }}>
            <label style={{ fontSize:12, color:'#64748b', display:'block', marginBottom:4 }}>Description *</label>
            <input required value={f.description} onChange={e=>setF({...f,description:e.target.value})}
              placeholder="e.g. Sales invoice INV-001"
              style={{ width:'100%', border:'1px solid #e2e8f0', borderRadius:8, padding:'9px 12px', fontSize:14 }}/>
          </div>

          <div style={{ marginBottom:8 }}>
            <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr 1fr 32px', gap:6, marginBottom:6 }}>
              {['Account','Type','Amount',''].map(h=>(
                <div key={h} style={{ fontSize:11, color:'#64748b', fontWeight:500 }}>{h}</div>
              ))}
            </div>
            {f.lines.map((line, i) => (
              <div key={i} style={{ display:'grid', gridTemplateColumns:'2fr 1fr 1fr 32px', gap:6, marginBottom:6 }}>
                <select value={line.account_id} onChange={e=>updateLine(i,'account_id',e.target.value)}
                  style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 8px', fontSize:12 }}>
                  <option value="">Select account</option>
                  {accounts.map(a=>(
                    <option key={a.id} value={a.id}>{a.code} — {a.name}</option>
                  ))}
                </select>
                <select value={line.type} onChange={e=>updateLine(i,'type',e.target.value)}
                  style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 8px', fontSize:12,
                    color: line.type==='debit'?'#1d4ed8':'#15803d', fontWeight:600 }}>
                  <option value="debit">Debit</option>
                  <option value="credit">Credit</option>
                </select>
                <input type="number" value={line.amount} onChange={e=>updateLine(i,'amount',e.target.value)}
                  style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 8px', fontSize:12 }}/>
                <button type="button" onClick={()=>removeLine(i)} disabled={f.lines.length<=2}
                  style={{ background:'none', border:'none', cursor:'pointer', color:'#94a3b8', padding:4 }}>
                  <X size={14}/>
                </button>
              </div>
            ))}
          </div>

          <button type="button" onClick={addLine}
            style={{ fontSize:12, color:'#3b82f6', background:'none', border:'1px dashed #93c5fd', borderRadius:6, padding:'5px 12px', cursor:'pointer', marginBottom:14 }}>
            + Add line
          </button>

          <div style={{ display:'flex', justifyContent:'space-between', background:'#f8fafc', borderRadius:8, padding:'10px 14px', marginBottom:14, fontSize:13 }}>
            <div>Total Debit: <strong style={{ color:'#1d4ed8' }}>₹{totalDebit.toLocaleString('en-IN')}</strong></div>
            <div>Total Credit: <strong style={{ color:'#15803d' }}>₹{totalCredit.toLocaleString('en-IN')}</strong></div>
            <div style={{ color: balanced?'#16a34a':'#dc2626', fontWeight:600, display:'flex', alignItems:'center', gap:4 }}>
              {balanced ? <><CheckCircle size={14}/> Balanced</> : '⚠ Not balanced'}
            </div>
          </div>

          {error && <p style={{ color:'#ef4444', fontSize:12, marginBottom:10 }}>{error}</p>}
          <div style={{ display:'flex', gap:8 }}>
            <button type="submit" disabled={loading||!balanced}
              style={{ flex:1, background: balanced?'#1e40af':'#94a3b8', color:'#fff', border:'none', borderRadius:8, padding:'10px', fontWeight:600, cursor: balanced?'pointer':'not-allowed', fontSize:14 }}>
              {loading ? 'Posting...' : 'Post Journal Entry'}
            </button>
            <button type="button" onClick={onClose}
              style={{ padding:'10px 16px', border:'1px solid #e2e8f0', borderRadius:8, cursor:'pointer' }}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Finance() {
  const [tab, setTab]         = useState('accounts')
  const [accounts, setAccounts] = useState([])
  const [journals, setJournals] = useState([])
  const [search, setSearch]   = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [showNewAcct, setShowNewAcct] = useState(false)
  const [showNewJournal, setShowNewJournal] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [aRes, jRes] = await Promise.all([
        api.get('/finance/accounts'),
        api.get('/finance/journals').catch(()=>({data:[]}))
      ])
      setAccounts(aRes.data)
      setJournals(jRes.data)
    } catch(e) {}
    setLoading(false)
  }

  useEffect(()=>{ load() },[])

  const filtered = accounts.filter(a => {
    const matchType = typeFilter==='all' || a.account_type===typeFilter
    const matchQ    = !search || a.code?.includes(search) || a.name?.toLowerCase().includes(search.toLowerCase())
    return matchType && matchQ
  })

  const counts = ACCOUNT_TYPES.reduce((acc,t) => ({...acc,[t]: accounts.filter(a=>a.account_type===t).length}),{})
  const fmt = (n) => '₹'+Number(n||0).toLocaleString('en-IN')

  return (
    <div style={{ padding:24, background:'#f8fafc', minHeight:'100vh' }}>
      {showNewAcct && <NewAccountModal onClose={()=>setShowNewAcct(false)} onSaved={()=>{setShowNewAcct(false);load()}}/>}
      {showNewJournal && <NewJournalModal accounts={accounts} onClose={()=>setShowNewJournal(false)} onSaved={()=>{setShowNewJournal(false);load()}}/>}

      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 }}>
        <div>
          <h1 style={{ fontSize:24, fontWeight:700, color:'#0f172a' }}>Finance</h1>
          <p style={{ color:'#64748b', fontSize:14 }}>GL Accounts, Journal Entries &amp; Financial Reports</p>
        </div>
        <div style={{ display:'flex', gap:8 }}>
          <button onClick={()=>setShowNewJournal(true)}
            style={{ display:'flex', alignItems:'center', gap:6, background:'#fff', border:'1px solid #e2e8f0', borderRadius:10, padding:'8px 16px', fontSize:14, fontWeight:600, cursor:'pointer' }}>
            <BookOpen size={15}/> New Journal
          </button>
          <button onClick={()=>setShowNewAcct(true)}
            style={{ display:'flex', alignItems:'center', gap:6, background:'#1e40af', color:'#fff', border:'none', borderRadius:10, padding:'8px 16px', fontSize:14, fontWeight:600, cursor:'pointer' }}>
            <Plus size={15}/> New Account
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))', gap:12, marginBottom:24 }}>
        <StatCard label="Total Accounts" value={accounts.length} color="#1e40af" icon={BookOpen}/>
        <StatCard label="Asset Accounts" value={counts.asset||0} color="#185FA5" icon={TrendingUp}/>
        <StatCard label="Income Accounts" value={counts.income||0} color="#3B6D11" icon={TrendingUp}/>
        <StatCard label="Expense Accounts" value={counts.expense||0} color="#854F0B" icon={TrendingDown}/>
        <StatCard label="Journal Entries" value={journals.length} color="#534AB7" icon={Scale}/>
      </div>

      {/* Tabs */}
      <div style={{ display:'flex', gap:4, marginBottom:16 }}>
        {[['accounts','GL Accounts'],['journals','Journal Entries'],['reports','Reports']].map(([key,label])=>(
          <button key={key} onClick={()=>setTab(key)}
            style={{ padding:'8px 20px', borderRadius:8, border:'none', cursor:'pointer', fontSize:14, fontWeight:600,
              background: tab===key ? '#1e40af' : '#fff',
              color: tab===key ? '#fff' : '#64748b',
              boxShadow: tab===key ? '0 2px 8px rgba(30,64,175,0.2)' : 'none'
            }}>{label}</button>
        ))}
      </div>

      {/* GL ACCOUNTS TAB */}
      {tab==='accounts' && (
        <div>
          {/* Type filter pills */}
          <div style={{ display:'flex', gap:6, flexWrap:'wrap', marginBottom:12 }}>
            {[['all','All',accounts.length], ...ACCOUNT_TYPES.map(t=>[t,t,counts[t]||0])].map(([val,label,cnt])=>(
              <button key={val} onClick={()=>setTypeFilter(val)}
                style={{
                  fontSize:12, padding:'5px 12px', borderRadius:20, cursor:'pointer', fontWeight:500,
                  border: typeFilter===val ? `1.5px solid ${TYPE_COLORS[val]?.dot||'#1e40af'}` : '1px solid #e2e8f0',
                  background: typeFilter===val ? (TYPE_COLORS[val]?.bg||'#EFF6FF') : '#fff',
                  color: typeFilter===val ? (TYPE_COLORS[val]?.text||'#1e40af') : '#64748b'
                }}>
                {label.charAt(0).toUpperCase()+label.slice(1)} <span style={{ opacity:0.7 }}>({cnt})</span>
              </button>
            ))}
          </div>

          {/* Search */}
          <div style={{ position:'relative', marginBottom:12 }}>
            <Search size={14} style={{ position:'absolute', left:12, top:'50%', transform:'translateY(-50%)', color:'#94a3b8' }}/>
            <input value={search} onChange={e=>setSearch(e.target.value)}
              placeholder="Search by account code or name..."
              style={{ width:'100%', paddingLeft:36, paddingRight:12, paddingTop:9, paddingBottom:9, border:'1px solid #e2e8f0', borderRadius:10, fontSize:13, background:'#fff', outline:'none' }}/>
          </div>

          {/* Accounts table */}
          <div style={{ background:'#fff', borderRadius:12, border:'1px solid #e2e8f0', overflow:'hidden' }}>
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead>
                <tr style={{ background:'#f8fafc', borderBottom:'1px solid #e2e8f0' }}>
                  {['Code','Account Name','Type','Category'].map(h=>(
                    <th key={h} style={{ padding:'10px 16px', textAlign:'left', fontSize:11, fontWeight:700, color:'#64748b', textTransform:'uppercase', letterSpacing:'0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} style={{ padding:40, textAlign:'center', color:'#94a3b8' }}>Loading...</td></tr>
                ) : filtered.length===0 ? (
                  <tr><td colSpan={4} style={{ padding:40, textAlign:'center', color:'#94a3b8' }}>No accounts found</td></tr>
                ) : filtered.map(a => {
                  const code = parseInt(a.code)
                  const category =
                    code<1100?'Cash & Bank': code<1200?'Receivables': code<1300?'Inventory':
                    code<1400?'Fixed Assets': code<1500?'Tax Assets': code<2100?'Current Liabilities':
                    code<2200?'Long-term Liabilities': code<4000?'Equity':
                    code<4100?'Operating Income': code<5000?'Other Income':
                    code<5100?'Cost of Goods': code<5200?'Payroll':
                    code<5300?'Admin Expenses': code<5400?'Sales Expenses':
                    code<5500?'Finance Costs':'Tax & Compliance'
                  return (
                    <tr key={a.id} style={{ borderBottom:'1px solid #f1f5f9' }}>
                      <td style={{ padding:'10px 16px', fontFamily:'monospace', fontSize:12, color:'#64748b', fontWeight:600 }}>{a.code}</td>
                      <td style={{ padding:'10px 16px', fontSize:13, fontWeight:500, color:'#1e293b' }}>{a.name}</td>
                      <td style={{ padding:'10px 16px' }}><TypeBadge type={a.account_type}/></td>
                      <td style={{ padding:'10px 16px', fontSize:12, color:'#94a3b8' }}>{category}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize:12, color:'#94a3b8', marginTop:8 }}>{filtered.length} accounts shown</div>
        </div>
      )}

      {/* JOURNALS TAB */}
      {tab==='journals' && (
        <div style={{ background:'#fff', borderRadius:12, border:'1px solid #e2e8f0', overflow:'hidden' }}>
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead>
              <tr style={{ background:'#f8fafc', borderBottom:'1px solid #e2e8f0' }}>
                {['Entry #','Date','Description','Amount','Lines'].map(h=>(
                  <th key={h} style={{ padding:'10px 16px', textAlign:'left', fontSize:11, fontWeight:700, color:'#64748b', textTransform:'uppercase', letterSpacing:'0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} style={{ padding:40, textAlign:'center', color:'#94a3b8' }}>Loading...</td></tr>
              ) : journals.length===0 ? (
                <tr><td colSpan={5} style={{ padding:40, textAlign:'center', color:'#94a3b8' }}>No journal entries yet — create one to start double-entry bookkeeping</td></tr>
              ) : journals.map(j=>(
                <tr key={j.id} style={{ borderBottom:'1px solid #f1f5f9' }}>
                  <td style={{ padding:'10px 16px', fontFamily:'monospace', fontSize:12, color:'#64748b' }}>{j.entry_number || `JE-${j.id}`}</td>
                  <td style={{ padding:'10px 16px', fontSize:13, color:'#64748b' }}>{j.entry_date ? new Date(j.entry_date).toLocaleDateString('en-IN') : '—'}</td>
                  <td style={{ padding:'10px 16px', fontSize:13, fontWeight:500 }}>{j.description}</td>
                  <td style={{ padding:'10px 16px', fontSize:13, fontWeight:600 }}>{fmt(j.total_amount)}</td>
                  <td style={{ padding:'10px 16px', fontSize:12, color:'#94a3b8' }}>{j.line_count || '—'} lines</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* REPORTS TAB */}
      {tab==='reports' && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
          {/* P&L summary */}
          <div style={{ background:'#fff', borderRadius:12, border:'1px solid #e2e8f0', padding:20 }}>
            <h3 style={{ fontSize:16, fontWeight:700, color:'#0f172a', marginBottom:16 }}>Profit &amp; Loss</h3>
            <div style={{ marginBottom:12 }}>
              <div style={{ fontSize:12, color:'#64748b', marginBottom:6, fontWeight:600 }}>INCOME ACCOUNTS (4xxx)</div>
              {accounts.filter(a=>a.account_type==='income').slice(0,6).map(a=>(
                <div key={a.id} style={{ display:'flex', justifyContent:'space-between', padding:'5px 0', borderBottom:'1px solid #f1f5f9', fontSize:13 }}>
                  <span style={{ color:'#475569' }}>{a.name}</span>
                  <span style={{ color:'#16a34a', fontWeight:500 }}>{a.code}</span>
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize:12, color:'#64748b', marginBottom:6, fontWeight:600 }}>EXPENSE ACCOUNTS (5xxx)</div>
              {accounts.filter(a=>a.account_type==='expense').slice(0,6).map(a=>(
                <div key={a.id} style={{ display:'flex', justifyContent:'space-between', padding:'5px 0', borderBottom:'1px solid #f1f5f9', fontSize:13 }}>
                  <span style={{ color:'#475569' }}>{a.name}</span>
                  <span style={{ color:'#dc2626', fontWeight:500 }}>{a.code}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Balance Sheet summary */}
          <div style={{ background:'#fff', borderRadius:12, border:'1px solid #e2e8f0', padding:20 }}>
            <h3 style={{ fontSize:16, fontWeight:700, color:'#0f172a', marginBottom:16 }}>Balance Sheet</h3>
            {[['ASSETS (1xxx)','asset','#185FA5'],['LIABILITIES (2xxx)','liability','#A32D2D'],['EQUITY (3xxx)','equity','#534AB7']].map(([label,type,color])=>(
              <div key={type} style={{ marginBottom:12 }}>
                <div style={{ fontSize:12, color:'#64748b', marginBottom:6, fontWeight:600 }}>{label}</div>
                {accounts.filter(a=>a.account_type===type).slice(0,4).map(a=>(
                  <div key={a.id} style={{ display:'flex', justifyContent:'space-between', padding:'5px 0', borderBottom:'1px solid #f1f5f9', fontSize:13 }}>
                    <span style={{ color:'#475569' }}>{a.name}</span>
                    <span style={{ color, fontWeight:500 }}>{a.code}</span>
                  </div>
                ))}
                {accounts.filter(a=>a.account_type===type).length > 4 && (
                  <div style={{ fontSize:11, color:'#94a3b8', padding:'4px 0' }}>
                    +{accounts.filter(a=>a.account_type===type).length-4} more accounts
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
