export let CURRENCY = "so'm"
export const setCurrency = (c) => { if (c) CURRENCY = c }

export const money = (v) => {
  const n = Number(v || 0)
  return n.toLocaleString('ru-RU').replace(/ /g, ' ')
}
export const fmtMoney = (v) => `${money(v)} ${CURRENCY}`
