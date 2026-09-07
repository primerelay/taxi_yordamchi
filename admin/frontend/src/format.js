export let CURRENCY = "so'm"
export const setCurrency = (c) => { if (c) CURRENCY = c }

export const money = (v) => {
  const n = Number(v || 0)
  return n.toLocaleString('ru-RU').replace(/ /g, ' ')
}
export const fmtMoney = (v) => `${money(v)} ${CURRENCY}`

export const fmtInterval = (seconds) => {
  const s = Number(seconds || 0)
  if (!s) return '—'
  if (s % 3600 === 0) return `${s / 3600} soat`
  if (s % 60 === 0) return `${s / 60} daqiqa`
  return `${s} soniya`
}
