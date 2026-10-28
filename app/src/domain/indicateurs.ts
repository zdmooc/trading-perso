/** Mêmes calculs que src/tradeperso/indicators.py (moyennes de Wilder, comme pandas ewm adjust=False). */

export function sma(x: number[], n: number): (number | null)[] {
  let somme = 0;
  return x.map((v, i) => {
    somme += v - (i >= n ? x[i - n] : 0);
    return i >= n - 1 ? somme / n : null;
  });
}

function wilder(x: number[], n: number): (number | null)[] {
  let m = 0;
  return x.map((v, i) => {
    m = i === 0 ? v : m + (v - m) / n;
    return i >= n - 1 ? m : null;
  });
}

export interface Hlc {
  h: number;
  l: number;
  c: number;
}

export function atr(b: Hlc[], n = 14): (number | null)[] {
  const tr = b.map((x, i) => (i === 0 ? x.h - x.l : Math.max(x.h - x.l, Math.abs(x.h - b[i - 1].c), Math.abs(x.l - b[i - 1].c))));
  return wilder(tr, n);
}

export function rsi(c: number[], n = 14): (number | null)[] {
  if (c.length < 2) return c.map(() => null);
  const d = c.slice(1).map((v, i) => v - c[i]);
  const g = wilder(d.map((v) => Math.max(v, 0)), n);
  const p = wilder(d.map((v) => Math.max(-v, 0)), n);
  return [null, ...g.map((x, i) => (x === null || p[i] === null ? null : p[i] === 0 ? 100 : 100 - 100 / (1 + x / (p[i] as number))))];
}
