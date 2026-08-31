export function Card({ label, value, accent }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 px-5 py-4">
      <div className="text-[13px] text-slate-400">{label}</div>
      <div className={`mt-1.5 text-2xl font-bold ${accent || 'text-slate-100'}`}>{value}</div>
    </div>
  )
}

const BADGE = {
  green: 'bg-green-500/15 text-green-400',
  red: 'bg-red-500/15 text-red-400',
  amber: 'bg-amber-500/15 text-amber-400',
  gray: 'bg-slate-500/15 text-slate-300',
  sky: 'bg-sky-500/15 text-sky-400',
}

export function Badge({ tone = 'gray', children }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE[tone]}`}>
      {children}
    </span>
  )
}

export function PayBadge({ status }) {
  if (status === 'paid') return <Badge tone="green">to'langan</Badge>
  if (status === 'expired') return <Badge tone="red">muddati tugagan</Badge>
  return <Badge tone="amber">to'lanmagan</Badge>
}

export function MailBadge({ user }) {
  if (user.active) return <Badge tone="green">▶ tarqatyapti</Badge>
  if (user.session) return <Badge tone="gray">to'xtatilgan</Badge>
  return <Badge tone="gray">akkaunt yo'q</Badge>
}

export function Spinner() {
  return (
    <div className="flex justify-center py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />
    </div>
  )
}

export const inputCls =
  'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-400'
export const btnCls =
  'rounded-lg bg-sky-400 px-4 py-2 text-sm font-semibold text-sky-950 hover:bg-sky-300 disabled:opacity-50'
export const btnGhostCls =
  'rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800'
