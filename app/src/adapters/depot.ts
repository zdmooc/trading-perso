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
