/** Mes trades : ceux que je dis avoir pris, avec leurs vrais résultats en points et en euros. */
export type TypeTrade = 'intraday' | 'swing';
export type Courtier = 'IG' | 'eToro';

export interface TradePerso {
  id: string;
  /** instant d'entrée (ms) */
  quand: number;
  symbole: string;
  type: TypeTrade;
  courtier: Courtier;
  sens: 1 | -1;
  entree: number;
  stop: number;
  objectif: number;
  /** contrats (IG) ou unités (eToro) */
  quantite: number;
  /** euros gagnés ou perdus par point */
  eurParPoint: number;
  sortie?: number;
  quandSortie?: number;
}

export function points(t: TradePerso, cours?: number): number | null {
  const fin = t.sortie ?? cours;
  return fin === undefined ? null : t.sens * (fin - t.entree);
}

export function euros(t: TradePerso, cours?: number): number | null {
  const p = points(t, cours);
  return p === null ? null : p * t.eurParPoint;
}

export interface Bilan {
  trades: number;
  gagnes: number;
  perdus: number;
  totalPts: number;
  totalEur: number;
  gainMoyEur: number | null;
  perteMoyEur: number | null;
}

export function bilan(liste: { pts: number; eur: number }[]): Bilan {
  const g = liste.filter((x) => x.eur > 0), p = liste.filter((x) => x.eur <= 0);
  const moy = (v: number[]) => (v.length ? v.reduce((a, b) => a + b, 0) / v.length : null);
  return {
    trades: liste.length, gagnes: g.length, perdus: p.length,
    totalPts: liste.reduce((a, x) => a + x.pts, 0), totalEur: liste.reduce((a, x) => a + x.eur, 0),
    gainMoyEur: moy(g.map((x) => x.eur)), perteMoyEur: moy(p.map((x) => x.eur)),
  };
}

/** Bilan de mes trades clôturés, pour un type. */
export function bilanPerso(trades: TradePerso[], type: TypeTrade): Bilan {
  return bilan(trades.filter((t) => t.type === type && t.sortie !== undefined)
    .map((t) => ({ pts: points(t) as number, eur: euros(t) as number })));
}
