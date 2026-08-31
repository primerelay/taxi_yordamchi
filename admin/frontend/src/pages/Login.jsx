import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../api.js'
import { inputCls } from '../ui.jsx'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { token } = await api.login(username, password)
      setToken(token)
      navigate('/')
    } catch (err) {
      setError(err.message || 'Login yoki parol xato')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={submit} className="w-80 rounded-2xl border border-slate-700 bg-slate-800 p-8">
        <h1 className="mb-6 text-center text-xl font-bold">🚕 Admin panel</h1>
        <label className="mb-1.5 block text-[13px] text-slate-400">Login</label>
        <input className={inputCls} value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
        <label className="mb-1.5 mt-4 block text-[13px] text-slate-400">Parol</label>
        <input className={inputCls} type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="mt-6 w-full rounded-lg bg-sky-400 py-2.5 font-bold text-sky-950 hover:bg-sky-300 disabled:opacity-50" disabled={loading}>
          {loading ? 'Kirilmoqda...' : 'Kirish'}
        </button>
        {error && <div className="mt-4 text-center text-sm text-red-400">{error}</div>}
      </form>
    </div>
  )
}
