import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { fmtMoney } from '../format.js'
import { PayBadge, Spinner, inputCls, btnCls, btnGhostCls } from '../ui.jsx'

function Row({ k, children }) {
  return (
    <div className="flex justify-between border-b border-slate-800 py-1.5 text-sm">
      <span className="text-slate-400">{k}</span>
      <span className="text-right">{children}</span>
    </div>
  )
}

export default function UserDetail() {
  const { id } = useParams()
  const [u, setU] = useState(null)
  const [err, setErr] = useState('')
  const [amount, setAmount] = useState('')
  const [months, setMonths] = useState('1')
  const [note, setNote] = useState('')
  const [paidUntil, setPaidUntil] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.user(id).then((d) => { setU(d); setPaidUntil(d.paid_until || '') }).catch((e) => setErr(e.message))
  useEffect(() => { load() }, [id])

  const pay = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const d = await api.pay(id, { amount: parseFloat(amount), months: parseInt(months || '0', 10), note })
      setU(d); setPaidUntil(d.paid_until || ''); setAmount(''); setNote(''); setMonths('1')
    } catch (er) { alert(er.message) } finally { setBusy(false) }
  }

  const saveDate = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const d = await api.setDate(id, paidUntil)
      setU(d)
    } catch (er) { alert(er.message) } finally { setBusy(false) }
  }

  if (err) return <div className="text-red-400">{err}</div>
  if (!u) return <Spinner />

  return (
    <div className="space-y-4">
      <Link to="/users" className="text-sm text-slate-400 hover:text-slate-200">← Foydalanuvchilar</Link>
      <h1 className="flex items-center gap-3 text-xl font-bold">
        {u.full_name || `ID ${u.user_id}`}
        <PayBadge status={u.pay_status} />
      </h1>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Ma'lumotlar</h2>
          <Row k="Telegram ID">{u.user_id}</Row>
          <Row k="Username">{u.username ? '@' + u.username : '—'}</Row>
          <Row k="Telefon">{u.phone || '—'}</Row>
          <Row k="Akkaunt">{u.session ? '✅ ulangan' : '❌ yo‘q'}</Row>
          <Row k="Tarqatish">{u.active ? '▶ faol' : '⏹ to‘xtagan'}</Row>
          <Row k="Interval">{u.interval_minutes || '—'} daqiqa</Row>
          <Row k="Tanlangan guruhlar">{u.groups.length} ta</Row>
          <Row k="Qo'shilgan">{u.created_at}</Row>
          <Row k="Oxirgi faollik">{u.last_active || '—'}</Row>
          <Row k="To'lov muddati">{u.paid_until || '—'}</Row>
          <Row k="Jami to'lagan">{fmtMoney(u.paid_total)}</Row>
          {u.message && (
            <div className="mt-3">
              <div className="text-sm text-slate-400">Xabar:</div>
              <div className="mt-1.5 whitespace-pre-wrap rounded-lg bg-slate-950 p-2.5 text-sm">{u.message}</div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <form onSubmit={pay} className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">💳 To'lov qo'shish</h2>
            <label className="mb-1 block text-[13px] text-slate-400">Summa</label>
            <input className={inputCls} type="number" step="any" required value={amount} onChange={(e) => setAmount(e.target.value)} />
            <label className="mb-1 mt-3 block text-[13px] text-slate-400">Necha oyga</label>
            <input className={inputCls} type="number" min="0" value={months} onChange={(e) => setMonths(e.target.value)} />
            <label className="mb-1 mt-3 block text-[13px] text-slate-400">Izoh (ixtiyoriy)</label>
            <input className={inputCls} value={note} onChange={(e) => setNote(e.target.value)} />
            <button className={btnCls + ' mt-4'} disabled={busy}>To'lovni qayd etish</button>
            <p className="mt-2.5 text-xs text-slate-400">
              To'lov muddati avtomatik uzaytiriladi (joriy muddatdan yoki bugundan boshlab).
            </p>
          </form>

          <form onSubmit={saveDate} className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">📅 Muddatni qo'lda belgilash</h2>
            <input className={inputCls} type="date" value={paidUntil} onChange={(e) => setPaidUntil(e.target.value)} />
            <button className={btnGhostCls + ' mt-3'} disabled={busy}>Saqlash</button>
          </form>
        </div>
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">To'lovlar tarixi</h2>
        <div className="overflow-x-auto">
        <table className="w-full min-w-[380px] text-sm">
          <thead className="text-xs uppercase text-slate-400">
            <tr>{['Sana', 'Summa', 'Muddat', 'Izoh'].map((h) => <th key={h} className="px-2 py-2 text-left">{h}</th>)}</tr>
          </thead>
          <tbody>
            {u.payments.map((p) => (
              <tr key={p.id} className="border-t border-slate-800">
                <td className="px-2 py-2">{p.paid_at}</td>
                <td className="px-2 py-2">{fmtMoney(p.amount)}</td>
                <td className="px-2 py-2">{p.months || '—'} oy</td>
                <td className="px-2 py-2">{p.note || '—'}</td>
              </tr>
            ))}
            {u.payments.length === 0 && (
              <tr><td colSpan={4} className="px-2 py-6 text-center text-slate-400">To'lovlar yo'q</td></tr>
            )}
          </tbody>
        </table>
        </div>
      </div>

      {u.groups.length > 0 && (
        <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Tanlangan guruhlar</h2>
          <div className="overflow-x-auto">
          <table className="w-full min-w-[320px] text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr><th className="px-2 py-2 text-left">Chat ID</th><th className="px-2 py-2 text-left">Nomi</th></tr>
            </thead>
            <tbody>
              {u.groups.map((g) => (
                <tr key={g.chat_id} className="border-t border-slate-800">
                  <td className="px-2 py-2">{g.chat_id}</td>
                  <td className="px-2 py-2">{g.title}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  )
}
