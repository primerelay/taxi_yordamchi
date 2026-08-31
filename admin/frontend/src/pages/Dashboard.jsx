import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney } from '../format.js'
import { Card, Spinner, btnGhostCls } from '../ui.jsx'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setErr(e.message))
  }, [])

  if (err) return <div className="text-red-400">{err}</div>
  if (!stats) return <Spinner />

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-bold">Boshqaruv paneli</h1>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Foydalanuvchilar</h2>
        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-5">
          <Card label="Jami foydalanuvchi" value={stats.total_users} />
          <Card label="Bugungi faol (DAU)" value={stats.dau} accent="text-green-400" />
          <Card label="Bugun qo'shilgan" value={stats.new_today} />
          <Card label="Akkaunt ulagan" value={stats.logged_in} />
          <Card label="Hozir tarqatyapti" value={stats.mailing_now} accent="text-sky-400" />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">To'lov va hisob-kitob</h2>
        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-5">
          <Card label="To'lagan (faol obuna)" value={stats.paying} accent="text-green-400" />
          <Card label="Muddati tugagan" value={stats.expired} accent="text-red-400" />
          <Card label="Bu oy tushum" value={fmtMoney(stats.revenue_month)} />
          <Card label="Jami tushum" value={fmtMoney(stats.revenue_total)} />
          <Card label="To'lovlar soni" value={stats.payments_count} />
        </div>
      </section>

      <div className="flex gap-3">
        <Link to="/users" className={btnGhostCls}>Foydalanuvchilar ro'yxati →</Link>
        <Link to="/payments" className={btnGhostCls}>To'lovlar tarixi →</Link>
      </div>
    </div>
  )
}
