/**
 * Swing (bougies journalières, positions de quelques jours) : mêmes règles que src/tradeperso/strategies.py.
 * Chaque règle donne, pour chaque bougie : signal à la clôture (entrée à l'ouverture suivante), stop et objectif.
 */
import { atr, rsi, sma } from './indicateurs';
import type { Bougie } from './plan';

export interface Calcul {
  entree: boolean[];
  stop: (number | null)[];
  objectif: (number | null)[];
}

export interface RegleSwing {
  cle: string;
  nom: string;
  sens: 1 | -1;
  calculer(b: Bougie[]): Calcul;
}

const nul = <T>(x: T | null | undefined): x is T => x !== null && x !== undefined && !Number.isNaN(x as number);

/** Moyenne 200 jours, remplacée par la 50 jours tant que l'historique est trop court. */
export function tendanceLongue(c: number[], lent = 200, court = 50): (number | null)[] {
  const l = sma(c, lent), k = sma(c, court);
  return l.map((v, i) => v ?? k[i]);
}

function decale<T>(x: (T | null)[], n = 1): (T | null)[] {
  return x.map((_, i) => (i >= n ? x[i - n] : null));
}

function glissant(x: number[], n: number, f: (v: number[]) => number): (number | null)[] {
  return x.map((_, i) => (i >= n - 1 ? f(x.slice(i - n + 1, i + 1)) : null));
}

const max = (v: number[]) => Math.max(...v);
const min = (v: number[]) => Math.min(...v);

function tendanceMm(b: Bougie[], sens: 1 | -1, lent = 200, kStop = 2): Calcul {
  const c = b.map((x) => x.c);
  const m20 = sma(c, 20), m50 = sma(c, 50), m200 = tendanceLongue(c, lent), a = atr(b);
  const entree = c.map((v, i) => {
    if (i === 0 || ![m20[i], m50[i], m20[i - 1], m50[i - 1], m200[i]].every(nul)) return false;
    const croise = sens > 0
      ? (m20[i] as number) > (m50[i] as number) && (m20[i - 1] as number) <= (m50[i - 1] as number)
      : (m20[i] as number) < (m50[i] as number) && (m20[i - 1] as number) >= (m50[i - 1] as number);
    return croise && (sens > 0 ? v > (m200[i] as number) : v < (m200[i] as number));
  });
  return niveaux3r(c, a, entree, sens, kStop);
}

function niveaux3r(c: number[], a: (number | null)[], entree: boolean[], sens: 1 | -1, kStop: number): Calcul {
  const stop = c.map((v, i) => (nul(a[i]) ? v - sens * kStop * (a[i] as number) : null));
  return { entree, stop, objectif: c.map((v, i) => (nul(stop[i]) ? v + 3 * (v - (stop[i] as number)) : null)) };
}

function cassure20j(b: Bougie[], sens: 1 | -1, n = 20, lent = 200, kStop = 2): Calcul {
  const c = b.map((x) => x.c);
  const m200 = tendanceLongue(c, lent), a = atr(b);
  const borne = decale(sens > 0 ? glissant(b.map((x) => x.h), n, max) : glissant(b.map((x) => x.l), n, min));
  const entree = c.map((v, i) => nul(borne[i]) && nul(m200[i]) &&
    (sens > 0 ? v > (borne[i] as number) && v > (m200[i] as number) : v < (borne[i] as number) && v < (m200[i] as number)));
  return niveaux3r(c, a, entree, sens, kStop);
}

function rsi2Repli(b: Bougie[]): Calcul {
  const c = b.map((x) => x.c);
  const m200 = sma(c, 200), a = atr(b), r2 = rsi(c, 2);
  return {
    entree: c.map((v, i) => nul(r2[i]) && nul(m200[i]) && (r2[i] as number) < 10 && v > (m200[i] as number)),
    stop: c.map((v, i) => (nul(a[i]) ? v - 2.5 * (a[i] as number) : null)),
    objectif: c.map((v, i) => (nul(a[i]) ? v + 1.5 * (a[i] as number) : null)),
  };
}

/** Repli sur la MM20 dans une tendance établie, entrée sur reprise, stop sous le creux du repli. */
function repli(b: Bougie[], sens: 1 | -1, objectifR = 3, lent = 200): Calcul {
  const c = b.map((x) => x.c * sens);
  const haut = b.map((x) => (sens > 0 ? x.h : -x.l)), bas = b.map((x) => (sens > 0 ? x.l : -x.h));
  const m20 = sma(c, 20), m50 = sma(c, 50), m200 = tendanceLongue(c, lent), a = atr(b);
  const touche = bas.map((v, i) => nul(m20[i]) && v <= (m20[i] as number));
  const out: Calcul = { entree: [], stop: [], objectif: [] };
  c.forEach((v, i) => {
    const tendance = i >= 5 && [m50[i], m200[i], m50[i - 5]].every(nul) &&
      v > (m50[i] as number) && (m50[i] as number) > (m200[i] as number) && (m50[i] as number) > (m50[i - 5] as number);
    const repliRecent = i >= 4 && touche.slice(i - 4, i + 1).some(Boolean);
    const reprise = i >= 1 && nul(m20[i]) && v > haut[i - 1] && v > (m20[i] as number);
    out.entree.push(tendance && repliRecent && reprise);
    if (i < 4 || !nul(a[i])) {
      out.stop.push(null);
      out.objectif.push(null);
      return;
    }
    const creux = min(bas.slice(i - 4, i + 1)) - 0.25 * (a[i] as number);
    const risque = Math.max(v - creux, 0.5 * (a[i] as number));
    out.stop.push((v - risque) * sens);
    out.objectif.push((v + objectifR * risque) * sens);
  });
  return out;
}

/** Règles envoyées par le scanner pour les indices (achats et ventes à découvert). */
export const REGLES_SWING: RegleSwing[] = [
  { cle: 'tendance_mm', nom: 'Croisement des moyennes 20 / 50 jours', sens: 1, calculer: (b) => tendanceMm(b, 1) },
  { cle: 'rsi2_repli', nom: 'Repli express (RSI 2 jours sous 10)', sens: 1, calculer: rsi2Repli },
  { cle: 'cassure_20j', nom: 'Cassure du plus haut 20 jours', sens: 1, calculer: (b) => cassure20j(b, 1) },
  { cle: 'repli_tendance', nom: 'Repli sur la moyenne 20 jours', sens: 1, calculer: (b) => repli(b, 1) },
  { cle: 'tendance_mm_vente', nom: 'Croisement des moyennes 20 / 50 jours (baisse)', sens: -1, calculer: (b) => tendanceMm(b, -1) },
  { cle: 'cassure_20j_vente', nom: 'Cassure du plus bas 20 jours', sens: -1, calculer: (b) => cassure20j(b, -1) },
];

export interface SignalSwing {
  regle: RegleSwing;
  /** clôture du signal : entrée prévue à l'ouverture suivante */
  cours: number;
  stop: number;
  objectif: number;
}

export interface Swing {
  /** date de la dernière clôture utilisée */
  date: string;
  cours: number;
  signaux: SignalSwing[];
  mm50: number | null;
  mm200: number | null;
  rsi: number | null;
  plusHaut20: number;
  plusBas20: number;
  tendance: 'haussière' | 'baissière' | 'sans direction nette';
  /** filtre de marché : achats seulement si le S&P 500 est au-dessus de sa moyenne 200 jours, ventes seulement en dessous */
  marcheHaussier: boolean | null;
}

/** Signaux à la dernière clôture de `b` (bougies terminées seulement). */
export function analyserSwing(b: Bougie[], date: string, marcheHaussier: boolean | null): Swing | null {
  if (b.length < 60) return null;
  const n = b.length - 1;
  const c = b.map((x) => x.c);
  const mm50 = sma(c, 50)[n], mm200 = sma(c, 200)[n], m20 = sma(c, 20)[n] as number;
  const signaux: SignalSwing[] = [];
  for (const r of REGLES_SWING) {
    if (marcheHaussier !== null && (r.sens > 0) !== marcheHaussier) continue;
    const k = r.calculer(b);
    if (k.entree[n] && nul(k.stop[n]) && nul(k.objectif[n])) signaux.push({ regle: r, cours: c[n], stop: k.stop[n] as number, objectif: k.objectif[n] as number });
  }
  const dernier = b.slice(-21, -1);
  const lent = mm200 ?? mm50;
  return {
    date, cours: c[n], signaux, mm50, mm200, rsi: rsi(c)[n],
    plusHaut20: Math.max(...dernier.map((x) => x.h)), plusBas20: Math.min(...dernier.map((x) => x.l)),
    tendance: lent !== null && c[n] > m20 && m20 > lent ? 'haussière' : lent !== null && c[n] < m20 && m20 < lent ? 'baissière' : 'sans direction nette',
    marcheHaussier,
  };
}
