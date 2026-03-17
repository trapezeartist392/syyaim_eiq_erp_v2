// frontend/src/pages/ForgotPassword.jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'

export default function ForgotPassword() {
  const [step, setStep]         = useState('email')   // email | sent | reset | done
  const [email, setEmail]       = useState('')
  const [token, setToken]       = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [showPwd, setShowPwd]   = useState(false)

  const sendReset = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try {
      await api.post('/auth/forgot-password', { email })
      setStep('sent')
    } catch(err) {
      setError(err.response?.data?.detail || 'Failed to send reset email')
    } finally { setLoading(false) }
  }

  const resetPassword = async (e) => {
    e.preventDefault()
    if (password !== confirm) { setError('Passwords do not match'); return }
    if (password.length < 8)  { setError('Password must be at least 8 characters'); return }
    setLoading(true); setError('')
    try {
      await api.post('/auth/reset-password', { token, new_password: password })
      setStep('done')
    } catch(err) {
      setError(err.response?.data?.detail || 'Invalid or expired token')
    } finally { setLoading(false) }
  }

  return (
    <div style={{
      minHeight:'100vh', background:'linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%)',
      display:'flex', alignItems:'center', justifyContent:'center', padding:16
    }}>
      <div style={{ width:'100%', maxWidth:420 }}>
        {/* Logo */}
        <div style={{ textAlign:'center', marginBottom:32 }}>
          <div style={{
            width:52, height:52, background:'#f59e0b', borderRadius:14,
            display:'flex', alignItems:'center', justifyContent:'center',
            margin:'0 auto 12px', fontSize:24
          }}>⚙</div>
          <div style={{ fontSize:22, fontWeight:700, color:'#fff' }}>Syyaim EIQ</div>
          <div style={{ fontSize:13, color:'#64748b', marginTop:2 }}>ERP Platform</div>
        </div>

        <div style={{
          background:'#fff', borderRadius:20, padding:32,
          boxShadow:'0 25px 50px rgba(0,0,0,0.4)'
        }}>

          {/* Step 1: Enter email */}
          {step === 'email' && (
            <>
              <h2 style={{ fontSize:20, fontWeight:700, color:'#0f172a', marginBottom:6 }}>Forgot password?</h2>
              <p style={{ fontSize:13, color:'#64748b', marginBottom:24 }}>
                Enter your email and we'll send you a reset link.
              </p>
              <form onSubmit={sendReset}>
                <div style={{ marginBottom:16 }}>
                  <label style={{ fontSize:12, fontWeight:600, color:'#374151', display:'block', marginBottom:5 }}>Email address</label>
                  <input
                    type="email" required value={email}
                    onChange={e=>setEmail(e.target.value)}
                    placeholder="you@company.com"
                    style={{ width:'100%', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 14px', fontSize:14, outline:'none' }}
                  />
                </div>
                {error && <p style={{ color:'#ef4444', fontSize:12, marginBottom:12 }}>{error}</p>}
                <button type="submit" disabled={loading} style={{
                  width:'100%', background:'#1e40af', color:'#fff', border:'none',
                  borderRadius:10, padding:'11px', fontWeight:700, fontSize:14,
                  cursor: loading?'not-allowed':'pointer', opacity: loading?0.7:1
                }}>
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>
            </>
          )}

          {/* Step 2: Email sent */}
          {step === 'sent' && (
            <>
              <div style={{ textAlign:'center', marginBottom:20 }}>
                <div style={{ fontSize:48, marginBottom:8 }}>📧</div>
                <h2 style={{ fontSize:20, fontWeight:700, color:'#0f172a', marginBottom:8 }}>Check your email</h2>
                <p style={{ fontSize:13, color:'#64748b' }}>
                  We sent a reset link to <strong>{email}</strong>. Check your inbox and paste the token below.
                </p>
              </div>
              <div style={{ marginBottom:16 }}>
                <label style={{ fontSize:12, fontWeight:600, color:'#374151', display:'block', marginBottom:5 }}>Reset Token</label>
                <input
                  value={token} onChange={e=>setToken(e.target.value)}
                  placeholder="Paste token from email"
                  style={{ width:'100%', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 14px', fontSize:13, outline:'none', fontFamily:'monospace' }}
                />
              </div>
              {error && <p style={{ color:'#ef4444', fontSize:12, marginBottom:12 }}>{error}</p>}
              <button onClick={()=>{ if(token) setStep('reset'); else setError('Paste the token from your email') }}
                style={{ width:'100%', background:'#1e40af', color:'#fff', border:'none', borderRadius:10, padding:'11px', fontWeight:700, fontSize:14, cursor:'pointer' }}>
                Continue
              </button>
              <button onClick={sendReset} disabled={loading}
                style={{ width:'100%', background:'none', border:'none', color:'#64748b', fontSize:12, marginTop:10, cursor:'pointer', padding:'6px' }}>
                {loading ? 'Resending...' : "Didn't receive it? Resend"}
              </button>
            </>
          )}

          {/* Step 3: Set new password */}
          {step === 'reset' && (
            <>
              <h2 style={{ fontSize:20, fontWeight:700, color:'#0f172a', marginBottom:6 }}>Set new password</h2>
              <p style={{ fontSize:13, color:'#64748b', marginBottom:24 }}>Choose a strong password for your account.</p>
              <form onSubmit={resetPassword}>
                <div style={{ marginBottom:14 }}>
                  <label style={{ fontSize:12, fontWeight:600, color:'#374151', display:'block', marginBottom:5 }}>New Password</label>
                  <div style={{ position:'relative' }}>
                    <input
                      type={showPwd?'text':'password'} required value={password}
                      onChange={e=>setPassword(e.target.value)}
                      placeholder="Min 8 characters"
                      style={{ width:'100%', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 40px 10px 14px', fontSize:14, outline:'none' }}
                    />
                    <button type="button" onClick={()=>setShowPwd(!showPwd)}
                      style={{ position:'absolute', right:12, top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', fontSize:16, color:'#94a3b8' }}>
                      {showPwd ? '🙈' : '👁'}
                    </button>
                  </div>
                  {/* Password strength */}
                  {password && (
                    <div style={{ marginTop:6 }}>
                      <div style={{ display:'flex', gap:3, marginBottom:3 }}>
                        {[1,2,3,4].map(i => (
                          <div key={i} style={{
                            flex:1, height:3, borderRadius:2,
                            background: password.length >= i*2 ?
                              (i<=2?'#ef4444': i===3?'#f59e0b':'#16a34a') : '#e2e8f0'
                          }}/>
                        ))}
                      </div>
                      <span style={{ fontSize:11, color:'#64748b' }}>
                        {password.length < 6 ? 'Too short' : password.length < 8 ? 'Weak' : password.length < 12 ? 'Good' : 'Strong'}
                      </span>
                    </div>
                  )}
                </div>
                <div style={{ marginBottom:20 }}>
                  <label style={{ fontSize:12, fontWeight:600, color:'#374151', display:'block', marginBottom:5 }}>Confirm Password</label>
                  <input
                    type={showPwd?'text':'password'} required value={confirm}
                    onChange={e=>setConfirm(e.target.value)}
                    placeholder="Repeat password"
                    style={{
                      width:'100%', borderRadius:10, padding:'10px 14px', fontSize:14, outline:'none',
                      border: confirm && confirm!==password ? '1.5px solid #ef4444' : '1.5px solid #e2e8f0'
                    }}
                  />
                  {confirm && confirm !== password && (
                    <p style={{ fontSize:11, color:'#ef4444', marginTop:3 }}>Passwords do not match</p>
                  )}
                </div>
                {error && <p style={{ color:'#ef4444', fontSize:12, marginBottom:12 }}>{error}</p>}
                <button type="submit" disabled={loading || password!==confirm}
                  style={{
                    width:'100%', background:'#1e40af', color:'#fff', border:'none',
                    borderRadius:10, padding:'11px', fontWeight:700, fontSize:14,
                    cursor: loading||password!==confirm ? 'not-allowed':'pointer',
                    opacity: loading||password!==confirm ? 0.6 : 1
                  }}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </form>
            </>
          )}

          {/* Step 4: Done */}
          {step === 'done' && (
            <div style={{ textAlign:'center' }}>
              <div style={{ fontSize:56, marginBottom:12 }}>✅</div>
              <h2 style={{ fontSize:20, fontWeight:700, color:'#0f172a', marginBottom:8 }}>Password reset!</h2>
              <p style={{ fontSize:13, color:'#64748b', marginBottom:24 }}>
                Your password has been updated successfully. You can now log in.
              </p>
              <Link to="/login" style={{
                display:'block', background:'#1e40af', color:'#fff', textDecoration:'none',
                borderRadius:10, padding:'11px', fontWeight:700, fontSize:14, textAlign:'center'
              }}>
                Back to Login
              </Link>
            </div>
          )}

          {/* Back to login */}
          {step !== 'done' && (
            <div style={{ textAlign:'center', marginTop:20 }}>
              <Link to="/login" style={{ fontSize:13, color:'#64748b', textDecoration:'none' }}>
                ← Back to login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
