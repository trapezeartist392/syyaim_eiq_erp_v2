import axios from 'axios'

// Detect tenant slug from subdomain or env
function getTenantSlug() {
  const host = window.location.hostname
  const baseDomain = import.meta.env.VITE_BASE_DOMAIN || 'syyaimeiq.com'

  if (host.endsWith(`.${baseDomain}`)) {
    const subdomain = host.slice(0, -(baseDomain.length + 1))
    if (subdomain && !['www', 'app', 'api', 'admin'].includes(subdomain)) {
      return subdomain
    }
  }
  // Fallback for local dev
  return import.meta.env.VITE_TENANT_SLUG || null
}

const tenantSlug = getTenantSlug()

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    ...(tenantSlug ? { 'X-Tenant-Slug': tenantSlug } : {}),
  },
})

// Attach JWT on every request
api.interceptors.request.use(cfg => {
  const t = localStorage.getItem('miq_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

// Handle 401 / 402
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('miq_token')
      localStorage.removeItem('miq_user')
      window.location.href = '/login'
    }
    if (err.response?.status === 402) {
      window.location.href = '/billing?suspended=true'
    }
    return Promise.reject(err)
  }
)

export default api
export { tenantSlug }
