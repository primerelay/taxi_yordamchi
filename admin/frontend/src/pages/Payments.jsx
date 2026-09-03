import { useState } from 'react'
import { useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney } from '../format.js'
import { Card, Spinner, inputCls, btnCls, btnGhostCls } from '../ui.jsx'

export default function Payments() {
  const [sp, setSp] = useSearchParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const dateFrom = sp.get('date_from') || ''
  const dateTo = sp.get('date_to') || ''
  const [from, setFrom] = useState(dateFrom)
  const [to, setTo] = useState(dateTo)

  useEffect(() => {
    setLoading(true)
    api.payments({ date_from: dateFrom, date_to: dateTo }).then(setData).finally(() => setLoading(false))
  }, [dateFrom, dateTo])

  const apply = (e) => {
    e.preventDefault()
    const next = {}
    if (from) next.date_from = from
    if (to) next.date_to = to
    setSp(next)
  }

  const userName = (p) => p.full_name || (p.username ? '@' + p.username : p.user_id)

  return (
    <div>
      <h1 className="text-xl font-bold">To'lovlar va hisob-kitob</h1>

      {/* Filtr */}
      <form onSubmit={apply} className="mt-4 flex flex-col gap-2.5 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="flex items-center gap-2">
          <label className="w-10 text-sm text-slate-400 sm:w-auto">Dan</label>
          <input className={inputCls + ' flex-1 sm:w-auto'} type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div className="flex items-center gap-2">
          <label className="w-10 text-sm text-slate-400 sm:w-auto">Gacha</label>
          <input className={inputCls + ' flex-1 sm:w-auto'} type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <div className="flex gap-2.5">
          <button className={btnCls + ' flex-1 sm:flex-none'}>Filtrlash</button>
          <button type="button" className={btnGhostCls} onClick={() => { setFrom(''); setTo(''); setSp({}) }}>Tozalash</button>
        </div>
      </form>

      {loading || !data ? <Spinner /> : (
        <>
          <div className="mt-5 grid grid-cols-2 gap-3.5 sm:max-w-lg">
            <Card label="Tanlangan davr tushumi" value={fmtMoney(data.total)} accent="text-green-400" />
            <Card label="To'lovlar soni" value={data.payments.length} />
          </div>

          {/* Mobil: kartochkalar */}
          <div className="mt-4 space-y-2.5 md:hidden">
            {data.payments.map((p) => (
              <div key={p.id} className="rounded-xl border border-slate-800 bg-slate-800/50 p-4">
                <div className="flex items-center justify-between gap-2">
                  <Link to={`/users/${p.user_id}`} className="truncate font-semibold text-sky-400">{userName(p)}</Link>
                  <span className="whitespace-nowrap font-semibold">{fmtMoney(p.amount)}</span>
                </div>
                <div className="mt-1 text-xs text-slate-400">
                  {p.paid_at} · {p.months || '—'} oy{p.phone ? ' · ' + p.phone : ''}
                </div>
                {p.note && <div className="mt-1 text-xs text-slate-300">{p.note}</div>}
              </div>
            ))}
            {data.payments.length === 0 && (
              <div className="rounded-xl border border-slate-800 py-8 text-center text-slate-400">To'lovlar topilmadi</div>
            )}
          </div>

          {/* Desktop: jadval */}
          <div className="mt-4 hidden overflow-x-auto rounded-xl border border-slate-800 md:block">
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  {['Sana', 'Foydalanuvchi', 'Telefon', 'Summa', 'Muddat', 'Izoh'].map((h) => (
                    <th key={h} className="px-3.5 py-3 text-left font-semibold whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.payments.map((p) => (
                  <tr key={p.id} className="border-t border-slate-800 bg-slate-800/40">
                    <td className="px-3.5 py-2.5 whitespace-nowrap">{p.paid_at}</td>
                    <td className="px-3.5 py-2.5">
                      <Link to={`/users/${p.user_id}`} className="text-sky-400 hover:underline">{userName(p)}</Link>
                    </td>
                    <td className="px-3.5 py-2.5">{p.phone || '—'}</td>
                    <td className="px-3.5 py-2.5 whitespace-nowrap">{fmtMoney(p.amount)}</td>
                    <td className="px-3.5 py-2.5">{p.months || '—'} oy</td>
                    <td className="px-3.5 py-2.5">{p.note || '—'}</td>
                  </tr>
                ))}
                {data.payments.length === 0 && (
                  <tr><td colSpan={6} className="px-3.5 py-8 text-center text-slate-400">To'lovlar topilmadi</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
