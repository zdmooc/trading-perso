/** Fichiers publiés par GitHub Actions dans le dépôt public (plan IG de 8h45, règles choisies par le test). */
import type { PlanIndice } from '../domain';

const BRUT = 'https://raw.githubusercontent.com/zdmooc/trading-perso/main/reports/plan';

async function json<T>(nom: string): Promise<T | null> {
  try {
    const r = await fetch(`${BRUT}/${nom}`, { cache: 'no-store' });
    return r.ok ? ((await r.json()) as T) : null;
  } catch {
    return null;
  }
}

export interface StatsRegle {
  trades: number;
  gagnes_pct: number;
  gain_moy: number;
  perdus_pct: number;
  perte_moy: number;
  total_pts: number;
  total_eur: number;
}

export interface StatsDepot {
  debut?: string;
  indices: Record<string, { choisie: string; regles: Record<string, StatsRegle> }>;
}

export const statsDepot = () => json<StatsDepot>('stats.json');

/** Plan de 8h45 en cours IG, s'il a été publié aujourd'hui. */
export const planDepot = (date: string) => json<{ date: string; indices: Record<string, PlanIndice> }>(`plan_${date}.json`);

export interface LigneJournal {
  date_signal: string;
  symbole: string;
  strategie: string;
  entree_prevue: number;
  stop: number;
  objectif: number;
  /** 1 achat, -1 vente (vide dans les anciennes lignes : achat) */
  sens: number;
  statut: string;
  date_entree: string;
  prix_entree: number;
  date_sortie: string;
  prix_sortie: number;
  motif: string;
  r: number;
}

const NUMERIQUES = ['entree_prevue', 'stop', 'objectif', 'sens', 'prix_entree', 'prix_sortie', 'r'];

/** Journal des signaux swing du scanner (reports/journal.csv), doublons retirés. */
export function lireJournal(texte: string): LigneJournal[] {
  const [tete, ...lignes] = texte.trim().split(/\r?\n/);
  const cols = tete.split(',');
  const vus = new Set<string>();
  const out: LigneJournal[] = [];
  for (const l of lignes) {
    const v = l.split(',');
    const o: Record<string, string | number> = {};
    cols.forEach((c, i) => (o[c] = NUMERIQUES.includes(c) ? (v[i] === '' || v[i] === undefined ? NaN : Number(v[i])) : v[i] ?? ''));
    if (Number.isNaN(o.sens)) o.sens = 1;
    const cle = `${o.date_signal}|${o.symbole}|${o.strategie}`;
    if (vus.has(cle)) continue;
    vus.add(cle);
    out.push(o as unknown as LigneJournal);
  }
  return out;
}

export async function journalDepot(): Promise<LigneJournal[]> {
  try {
    const r = await fetch('https://raw.githubusercontent.com/zdmooc/trading-perso/main/reports/journal.csv', { cache: 'no-store' });
    return r.ok ? lireJournal(await r.text()) : [];
  } catch {
    return [];
  }
}

export interface LignePlan {
  date: string;
  indice: string;
  sens: string;
  entree: number;
  heure: string;
  sortie: number;
  motif: string;
  pts: number;
  euros: number;
  statut: string;
}

/** Résultats réels du plan intraday (reports/plan/journal.csv, tenu par plan.yml). */
export function lirePlanJournal(texte: string): LignePlan[] {
  const [tete, ...lignes] = texte.trim().split(/\r?\n/);
  const cols = tete.split(',');
  return lignes.filter(Boolean).map((l) => {
    const v = l.split(',');
    const o: Record<string, string | number> = {};
    cols.forEach((c, i) => (o[c] = ['entree', 'sortie', 'pts', 'euros'].includes(c) ? (v[i] ? Number(v[i]) : NaN) : v[i] ?? ''));
    return o as unknown as LignePlan;
  });
}

export async function planJournalDepot(): Promise<LignePlan[]> {
  try {
    const r = await fetch(`${BRUT}/journal.csv`, { cache: 'no-store' });
    return r.ok ? lirePlanJournal(await r.text()) : [];
  } catch {
    return [];
  }
}
