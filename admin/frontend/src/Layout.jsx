import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api, clearToken } from './api.js'
import { setCurrency } from './format.js'

const TABS = [
  { to: '/', end: true, icon: '📊', label: 'Boshqaruv' },
  { to: '/users', end: false, icon: '👥', label: 'Foydalanuvchilar' },
  { to: '/payments', end: false, icon: '💳', label: "To'lovlar" },
]

export default function Layout() {
  const navigate = useNavigate()
  const [admin, setAdmin] = useState('')

  useEffect(() => {
    api.me().then((d) => { setAdmin(d.username); setCurrency(d.currency) }).catch(() => {})
  }, [])

  const logout = () => { clearToken(); navigate('/login') }

  const topLink = ({ isActive }) =>
    'px-1 py-1.5 border-b-2 transition-colors ' +
    (isActive ? 'border-sky-400 text-white' : 'border-transparent text-slate-400 hover:text-slate-200')

  const bottomLink = ({ isActive }) =>
    'flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[11px] transition-colors ' +
    (isActive ? 'text-sky-400' : 'text-slate-400')

  return (
    <div className="min-h-full">
      {/* Header */}
      <header className="sticky top-0 z-20 flex items-center gap-6 border-b border-slate-800 bg-slate-900/95 px-4 py-3 backdrop-blur sm:px-6">
        <span className="whitespace-nowrap text-base font-bold sm:text-lg">🚕 Taxi Yordamchi</span>
        <nav className="hidden gap-6 sm:flex">
          {TABS.map((t) => (
            <NavLink key={t.to} to={t.to} end={t.end} className={topLink}>{t.label}</NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-sm text-slate-400">
          {admin && <span className="hidden sm:inline">{admin}</span>}
          <button onClick={logout} className="rounded-lg px-2 py-1 text-sky-400 hover:bg-slate-800">
            Chiqish
          </button>
        </div>
      </header>

      {/* Content (pastki nav uchun mobil pastki padding) */}
      <main className="mx-auto max-w-6xl px-4 py-5 pb-24 sm:px-6 sm:pb-6">
        <Outlet />
      </main>

      {/* Pastki tab-bar (faqat mobil) */}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-slate-800 bg-slate-900/95 backdrop-blur sm:hidden">
        {TABS.map((t) => (
          <NavLink key={t.to} to={t.to} end={t.end} className={bottomLink}>
            <span className="text-xl leading-none">{t.icon}</span>
            {t.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
