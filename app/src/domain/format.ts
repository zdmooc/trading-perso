/** Format français : espace pour les milliers, virgule décimale, signe moins typographique. */
export function nombre(x: number, dec?: number): string {
  const d = dec ?? (Math.abs(x) >= 1000 ? 0 : 2);
  const [ent, frac] = Math.abs(x).toFixed(d).split('.');
  const groupes = ent.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  return (x < 0 && Number(Math.abs(x).toFixed(d)) !== 0 ? '−' : '') + groupes + (frac ? `,${frac}` : '');
}

const signe = (x: number) => (x >= 0 ? '+' : '−');

export function pts(x: number): string {
  return `${signe(x)}${nombre(Math.abs(x), 0)} pts`;
}

export function eur(x: number): string {
  return `${signe(x)}${nombre(Math.abs(x), 0)} €`;
}

/** Toujours les points à côté du pourcentage : « +120 pts (+0,5 %) ». */
export function variation(ecart: number, base: number): string {
  const pct = (100 * ecart) / base;
  return `${pts(ecart)} (${signe(pct)}${nombre(Math.abs(pct), 1)} %)`;
}
