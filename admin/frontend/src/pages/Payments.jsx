import { useEffect, useState } from 'react'
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
    api.payments({ date_from: dateFrom, date_to: dateTo })
      .then(setData)
      .finally(() => setLoading(false))
  }, [dateFrom, dateTo])

  const apply = (e) => {
    e.preventDefault()
    const next = {}
    if (from) next.date_from = from
    if (to) next.date_to = to
    setSp(next)
  }

  return (
    <div>
      <h1 className="text-xl font-bold">To'lovlar va hisob-kitob</h1>

      <form onSubmit={apply} className="mt-4 flex flex-wrap items-center gap-2.5">
        <label className="text-sm text-slate-400">Dan</label>
        <input className={inputCls + ' w-auto'} type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        <label className="text-sm text-slate-400">Gacha</label>
        <input className={inputCls + ' w-auto'} type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        <button className={btnCls}>Filtrlash</button>
        <button type="button" className={btnGhostCls} onClick={() => { setFrom(''); setTo(''); setSp({}) }}>Tozalash</button>
      </form>

      {loading || !data ? <Spinner /> : (
        <>
          <div className="mt-5 grid grid-cols-2 gap-3.5 sm:max-w-lg">
            <Card label="Tanlangan davr tushumi" value={fmtMoney(data.total)} accent="text-green-400" />
            <Card label="To'lovlar soni" value={data.payments.length} />
          </div>

          <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  {['Sana', 'Foydalanuvchi', 'Telefon', 'Summa', 'Muddat', 'Izoh'].map((h) => (
                    <th key={h} className="px-3.5 py-3 text-left font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.payments.map((p) => (
                  <tr key={p.id} className="border-t border-slate-800 bg-slate-800/40">
                    <td className="px-3.5 py-2.5">{p.paid_at}</td>
                    <td className="px-3.5 py-2.5">
                      <Link to={`/users/${p.user_id}`} className="text-sky-400 hover:underline">
                        {p.full_name || (p.username ? '@' + p.username : p.user_id)}
                      </Link>
                    </td>
                    <td className="px-3.5 py-2.5">{p.phone || '—'}</td>
                    <td className="px-3.5 py-2.5">{fmtMoney(p.amount)}</td>
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
