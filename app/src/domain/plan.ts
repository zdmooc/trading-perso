/**
 * Plan du jour : cassure (ou rejet) du plus haut / plus bas de la séance de la veille, objectif 3 fois le risque.
 * Portage fidèle de src/tradeperso/plan.py (ordres, seances, rejouer, preparer). Lecture seule : aucun ordre passé.
 */
import { atr, sma } from './indicateurs';
import { paris } from './temps';

export const RATIO = 3;

export interface Bougie {
  /** instant UTC en ms */
  t: number;
  o: number;
  h: number;
  l: number;
  c: number;
}

export interface Indice {
  symbole: string;
  nom: string;
  drapeau: string;
  /** première et dernière heure de bougie de la séance (heure de Paris) */
  heures: [number, number];
  debutMin: number;
  finEntree: number;
  /** contrats du plan : euros par point */
  taille: number;
  spread: number;
  fenetre: string;
}

export const INDICES: Indice[] = [
  { symbole: '^GDAXI', nom: 'DAX 40', drapeau: '🇩🇪', heures: [9, 17], debutMin: 0, finEntree: 15, taille: 0.5, spread: 1.2, fenetre: 'entrée 9h-16h, tout fermé à 17h30' },
  { symbole: '^NDX', nom: 'Nasdaq 100', drapeau: '🇺🇸', heures: [15, 21], debutMin: 30, finEntree: 20, taille: 0.5, spread: 1.0, fenetre: 'entrée 15h30-21h, tout fermé à 22h' },
  { symbole: '^GSPC', nom: 'S&P 500', drapeau: '🇺🇸', heures: [15, 21], debutMin: 30, finEntree: 20, taille: 1, spread: 0.4, fenetre: 'entrée 15h30-21h, tout fermé à 22h' },
];

/** Règle choisie par le test de 2 ans (reports/plan/stats.json), si le dépôt est injoignable. */
export const REGLES_PAR_DEFAUT: Record<string, string> = {
  '^GDAXI': 'cassure-0.25-tendance',
  '^NDX': 'cassure-0.25-aucun',
  '^GSPC': 'cassure-0.25-aucun',
};

export interface Ordre {
  /** 1 achat, -1 vente */
  sens: 1 | -1;
  niveau: number;
  /** « haut » : déclenché si le cours monte jusqu'au niveau ; « bas » : s'il descend */
  cote: 'haut' | 'bas';
  /** en points */
  risque: number;
}

export interface Trade {
  sens: 1 | -1;
  entree: number;
  stop: number;
  objectif: number;
  sortie: number;
  motif: 'stop' | 'objectif' | 'clôture' | 'en cours';
  heure: string;
  pts: number;
}

export interface PlanIndice {
  source: string;
  regle: string;
  veille: string;
  cloture: number;
  ordres: Ordre[];
}

export function ordres(cle: string, haut: number, bas: number, a: number, tendance: number): Ordre[] {
  const [type, k, filtre] = cle.split('-');
  const r = Number(k) * a;
  let liste: Ordre[] = type === 'cassure'
    ? [{ sens: 1, niveau: haut + 0.1 * a, cote: 'haut', risque: r }, { sens: -1, niveau: bas - 0.1 * a, cote: 'bas', risque: r }]
    : [{ sens: -1, niveau: haut, cote: 'haut', risque: r }, { sens: 1, niveau: bas, cote: 'bas', risque: r }];
  if (filtre === 'tendance') liste = liste.filter((o) => o.sens === tendance);
  return liste;
}

/** Bougies de chaque séance, de heures[0]h{debutMin} à la fin de la bougie de heures[1]h, par date de Paris. */
export function seances(b: Bougie[], ind: Pick<Indice, 'heures' | 'debutMin'>): Map<string, Bougie[]> {
  const out = new Map<string, Bougie[]>();
  for (const x of b) {
    const p = paris(x.t);
    if (p.heure * 60 + p.minute < ind.heures[0] * 60 + ind.debutMin || p.heure > ind.heures[1]) continue;
    out.set(p.date, [...(out.get(p.date) ?? []), x]);
  }
  return out;
}

/** Rejoue une séance : un seul trade, le premier niveau touché. */
export function rejouer(barres: Bougie[], liste: Ordre[], finEntree: number, spread: number, fini = true): Trade | null {
  let pos: Trade | null = null;
  for (const b of barres) {
    if (pos === null) {
      const p = paris(b.t);
      if (p.heure > finEntree) continue;
      const touches = liste.filter((o) => (o.cote === 'haut' ? b.h >= o.niveau : b.l <= o.niveau));
      if (!touches.length) continue;
      const o = touches.reduce((m, x) => (Math.abs(b.o - x.niveau) < Math.abs(b.o - m.niveau) ? x : m));
      const entree = o.cote === 'haut' ? Math.max(b.o, o.niveau) : Math.min(b.o, o.niveau);
      pos = {
        sens: o.sens, entree, stop: entree - o.sens * o.risque, objectif: entree + o.sens * RATIO * o.risque,
        sortie: NaN, motif: 'en cours', heure: `${String(p.heure).padStart(2, '0')}h${p.minute ? String(p.minute).padStart(2, '0') : ''}`, pts: NaN,
      };
      if (o.sens > 0 ? b.c <= pos.stop : b.c >= pos.stop) {
        pos.sortie = pos.stop;
        pos.motif = 'stop';
        break;
      }
      continue;
    }
    if (pos.sens > 0 ? b.l <= pos.stop : b.h >= pos.stop) {
      pos.sortie = pos.stop;
      pos.motif = 'stop';
      break;
    }
    if (pos.sens > 0 ? b.h >= pos.objectif : b.l <= pos.objectif) {
      pos.sortie = pos.objectif;
      pos.motif = 'objectif';
      break;
    }
  }
  if (pos === null) return null;
  if (Number.isNaN(pos.sortie)) {
    pos.sortie = barres[barres.length - 1].c;
    pos.motif = fini ? 'clôture' : 'en cours';
  }
  pos.pts = pos.sens * (pos.sortie - pos.entree) - spread;
  return pos;
}

/** Bougies journalières indexées par date de Paris. */
function parDate(d: Bougie[]): { date: string; b: Bougie }[] {
  return d.map((b) => ({ date: paris(b.t).date, b }));
}

/** Niveaux du jour, calculés sur la dernière séance terminée avant `jour`. */
export function preparer(ind: Indice, jour: string, quotidien: Bougie[], intraday: Bougie[], regle: string): PlanIndice | null {
  const ses = seances(intraday, ind);
  const passees = [...ses.keys()].filter((j) => j < jour).sort();
  const jours = parDate(quotidien);
  const a = atr(quotidien);
  const m20 = sma(quotidien.map((b) => b.c), 20);
  let i = jours.length - 1;
  while (i >= 0 && (jours[i].date >= jour || a[i] === null || m20[i] === null)) i--;
  if (!passees.length || i < 0) return null;
  const g = ses.get(passees[passees.length - 1]) as Bougie[];
  const tendance = jours[i].b.c > (m20[i] as number) ? 1 : -1;
  return {
    source: 'Yahoo', regle, veille: passees[passees.length - 1], cloture: g[g.length - 1].c,
    ordres: ordres(regle, Math.max(...g.map((b) => b.h)), Math.min(...g.map((b) => b.l)), a[i] as number, tendance),
  };
}

/** Pivots classiques calculés sur la semaine précédant `jour`. */
export function pivotsSemaine(quotidien: Bougie[], jour: string): Record<string, number> {
  const d = new Date(`${jour}T12:00:00Z`);
  const lundi = new Date(d.getTime() - ((d.getUTCDay() + 6) % 7) * 86_400_000).toISOString().slice(0, 10);
  const avant = new Date(Date.parse(`${lundi}T12:00:00Z`) - 7 * 86_400_000).toISOString().slice(0, 10);
  const w = parDate(quotidien).filter((x) => x.date < lundi && x.date >= avant).map((x) => x.b);
  if (!w.length) return {};
  const hi = Math.max(...w.map((b) => b.h)), lo = Math.min(...w.map((b) => b.l)), cl = w[w.length - 1].c;
  const p = (hi + lo + cl) / 3;
  return { R2: p + hi - lo, R1: 2 * p - lo, P: p, S1: 2 * p - hi, S2: p - (hi - lo) };
}
