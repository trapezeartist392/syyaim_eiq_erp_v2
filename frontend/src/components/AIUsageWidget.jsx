// frontend/src/components/AIUsageWidget.jsx
// Shows AI usage meter in the sidebar or Agents page

import { useState, useEffect } from 'react'
import api from '../utils/api'

export default function AIUsageWidget() {
  const [usage, setUsage] = useState(null)

  useEffect(() => {
    api.get('/agents/usage')
      .then(r => setUsage(r.data))
      .catch(() => {})
  }, [])

  if (!usage) return null

  const pct = Math.min(100, Math.round((usage.used_today / usage.limit) * 100))
  const color = pct >= 90 ? '#ef4444' : pct >= 70 ? '#f59e0b' : '#22c55e'

  return (
    <div style={{
      background: '#0f172a', border: '1px solid #1e3a5f',
      borderRadius: 10, padding: '12px 16px', margin: '8px 0'
    }}>
      <div style={{ display:'flex', justifyContent:'space-between', marginBottom: 6 }}>
        <span style={{ color:'#94a3b8', fontSize: 12 }}>AI Calls Today</span>
        <span style={{ color:'#e2e8f0', fontSize: 12, fontWeight: 600 }}>
          {usage.used_today} / {usage.limit}
        </span>
      </div>
      <div style={{ background:'#1e293b', borderRadius: 4, height: 6 }}>
        <div style={{
          width: `${pct}%`, height: 6, borderRadius: 4,
          background: color, transition: 'width 0.4s ease'
        }}/>
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', marginTop: 5 }}>
        <span style={{ color:'#475569', fontSize: 11 }}>{usage.plan} plan</span>
        <span style={{ color: color, fontSize: 11 }}>{usage.remaining_today} remaining</span>
      </div>
      {usage.remaining_today === 0 && (
        <div style={{
          marginTop: 8, background:'#7f1d1d', borderRadius: 6,
          padding:'6px 10px', fontSize: 11, color:'#fca5a5', textAlign:'center'
        }}>
          Daily limit reached — resets at midnight UTC
        </div>
      )}
    </div>
  )
}
