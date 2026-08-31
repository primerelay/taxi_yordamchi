const TOKEN_KEY = 'taxi_admin_token'

// Ishlab chiqarishda (Vercel) backend boshqa domenda bo'ladi — VITE_API_BASE dan olinadi.
// Dev'da bo'sh qoldiriladi va Vite proxy /api ni backendga uzatadi.
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

async function req(path, opts = {}) {
  const token = getToken()
  const res = await fetch(API_BASE + '/api' + path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  })
  if (res.status === 401) {
    clearToken()
    if (location.pathname !== '/login') location.href = '/login'
    throw new Error('Avtorizatsiya kerak')
  }
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: 'Xatolik' }))
    throw new Error(e.detail || 'Xatolik')
  }
  return res.status === 204 ? null : res.json()
}

const qs = (params) =>
  '?' + new URLSearchParams(Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v != null)
  )).toString()

export const api = {
  login: (username, password) =>
    req('/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  me: () => req('/me'),
  stats: () => req('/stats'),
  users: (params) => req('/users' + qs(params)),
  user: (id) => req('/users/' + id),
  pay: (id, body) => req(`/users/${id}/pay`, { method: 'POST', body: JSON.stringify(body) }),
  setDate: (id, paid_until) =>
    req(`/users/${id}/set-date`, { method: 'POST', body: JSON.stringify({ paid_until }) }),
  payments: (params) => req('/payments' + qs(params)),
}
