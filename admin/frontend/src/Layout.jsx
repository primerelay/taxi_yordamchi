import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api, clearToken } from './api.js'
import { setCurrency } from './format.js'

export default function Layout() {
  const navigate = useNavigate()
  const [admin, setAdmin] = useState('')

  useEffect(() => {
    api.me()
      .then((d) => { setAdmin(d.username); setCurrency(d.currency) })
      .catch(() => {})
  }, [])

  const logout = () => { clearToken(); navigate('/login') }

  const link = ({ isActive }) =>
    'px-1 py-1.5 border-b-2 ' +
    (isActive ? 'border-sky-400 text-white' : 'border-transparent text-slate-400 hover:text-slate-200')

  return (
    <div className="min-h-full">
      <nav className="flex items-center gap-6 border-b border-slate-800 bg-slate-900 px-6 py-3.5">
        <span className="text-lg font-bold">🚕 Taxi Yordamchi</span>
        <NavLink to="/" end className={link}>Boshqaruv</NavLink>
        <NavLink to="/users" className={link}>Foydalanuvchilar</NavLink>
        <NavLink to="/payments" className={link}>To'lovlar</NavLink>
        <div className="ml-auto text-sm text-slate-400">
          {admin && <span>{admin} · </span>}
          <button onClick={logout} className="text-sky-400 hover:underline">Chiqish</button>
        </div>
      </nav>
      <main className="mx-auto max-w-6xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  )
}
