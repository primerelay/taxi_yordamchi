import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { MailBadge, PayBadge, Spinner, inputCls, btnCls, btnGhostCls } from '../ui.jsx'

const STATUS_OPTS = [
  ['all', 'Barchasi'], ['paid', "To'lagan"], ['expired', 'Muddati tugagan'],
  ['unpaid', "To'lamagan"], ['active_today', 'Bugun faol'],
  ['mailing', 'Tarqatyapti'], ['logged_in', 'Akkaunt ulagan'],
]
const SORT_OPTS = [
  ['last_active', 'Oxirgi faollik'], ['created_at', "Qo'shilgan sana"], ['paid_until', "To'lov muddati"],
]

export default function Users() {
  const navigate = useNavigate()
  const [sp, setSp] = useSearchParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const search = sp.get('search') || ''
  const status = sp.get('status') || 'all'
  const sort = sp.get('sort') || 'last_active'
  const page = parseInt(sp.get('page') || '1', 10)

  const [searchInput, setSearchInput] = useState(search)

  useEffect(() => {
    setLoading(true)
    api.users({ search, status, sort, page })
      .then(setData)
      .finally(() => setLoading(false))
  }, [search, status, sort, page])

  const update = (patch) => {
    const next = { search, status, sort, page: 1, ...patch }
    setSp(Object.fromEntries(Object.entries(next).filter(([, v]) => v && v !== 'all' && v !== '')))
  }

  return (
    <div>
      <h1 className="text-xl font-bold">
        Foydalanuvchilar <span className="text-base font-normal text-slate-400">({data?.total ?? 0})</span>
      </h1>

      <div className="mt-4 flex flex-wrap items-center gap-2.5">
        <form
          onSubmit={(e) => { e.preventDefault(); update({ search: searchInput }) }}
          className="flex gap-2"
        >
          <input
            className={inputCls + ' w-56'}
            placeholder="ID, ism, username, tel..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button className={btnCls}>Qidirish</button>
        </form>
        <select className={inputCls + ' w-auto'} value={status} onChange={(e) => update({ status: e.target.value })}>
          {STATUS_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select className={inputCls + ' w-auto'} value={sort} onChange={(e) => update({ sort: e.target.value })}>
          {SORT_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <button className={btnGhostCls} onClick={() => { setSearchInput(''); setSp({}) }}>Tozalash</button>
      </div>

      {loading ? <Spinner /> : (
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                {['ID', 'Ism', 'Username', 'Telefon', 'Guruh', 'Holat', "To'lov", 'Muddat', 'Oxirgi faollik'].map((h) => (
                  <th key={h} className="px-3.5 py-3 text-left font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.users.map((u) => (
                <tr
                  key={u.user_id}
                  onClick={() => navigate(`/users/${u.user_id}`)}
                  className="cursor-pointer border-t border-slate-800 bg-slate-800/40 hover:bg-slate-700/50"
                >
                  <td className="px-3.5 py-2.5">{u.user_id}</td>
                  <td className="px-3.5 py-2.5">{u.full_name || '—'}</td>
                  <td className="px-3.5 py-2.5">{u.username ? '@' + u.username : '—'}</td>
                  <td className="px-3.5 py-2.5">{u.phone || '—'}</td>
                  <td className="px-3.5 py-2.5">{u.groups_count}</td>
                  <td className="px-3.5 py-2.5"><MailBadge user={u} /></td>
                  <td className="px-3.5 py-2.5"><PayBadge status={u.pay_status} /></td>
                  <td className="px-3.5 py-2.5">{u.paid_until || '—'}</td>
                  <td className="px-3.5 py-2.5 text-slate-400">{u.last_active || '—'}</td>
                </tr>
              ))}
              {data.users.length === 0 && (
                <tr><td colSpan={9} className="px-3.5 py-8 text-center text-slate-400">Topilmadi</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {data && data.pages > 1 && (
        <div className="mt-4 flex items-center gap-3">
          <button
            className={btnGhostCls}
            disabled={page <= 1}
            onClick={() => setSp({ search, status, sort, page: page - 1 })}
          >← Oldingi</button>
          <span className="text-slate-400">{page} / {data.pages}</span>
          <button
            className={btnGhostCls}
            disabled={page >= data.pages}
            onClick={() => setSp({ search, status, sort, page: page + 1 })}
          >Keyingi →</button>
        </div>
      )}
    </div>
  )
}
