/**
 * Charge tout l'écran : cours Yahoo, plan du jour (celui d'IG publié à 8h45 s'il existe, sinon calculé
 * sur le téléphone avec la même règle), état de chaque indice. Lecture seule : aucun ordre passé.
 */
import { type Bougie, INDICES, type PlanIndice, REGLES_PAR_DEFAUT, type Resume, paris, preparer, resumer, weekEnd } from '../domain';
import type { StatsDepot, StatsRegle } from '../adapters/depot';

export interface Sources {
  bougies(symbole: string, periode: string, intervalle: string): Promise<Bougie[]>;
  stats(): Promise<StatsDepot | null>;
  plan(date: string): Promise<{ indices: Record<string, PlanIndice> } | null>;
}

export interface Marche {
  maintenant: number;
  resumes: Resume[];
  quotidien: Record<string, Bougie[]>;
  stats: Record<string, StatsRegle | undefined>;
  debutTest?: string;
  erreurs: string[];
}

export async function charger(src: Sources, maintenant = Date.now()): Promise<Marche> {
  const date = paris(maintenant).date;
  const ferme = weekEnd(maintenant);
  const [stats, publie] = await Promise.all([src.stats(), ferme ? null : src.plan(date)]);
  const erreurs: string[] = [];
  const quotidien: Record<string, Bougie[]> = {};
  const resumes = await Promise.all(INDICES.map(async (ind) => {
    const [d, h] = await Promise.all([
      src.bougies(ind.symbole, '1y', '1d').catch((e: Error) => (erreurs.push(e.message), [] as Bougie[])),
      src.bougies(ind.symbole, '5d', '30m').catch((e: Error) => (erreurs.push(e.message), [] as Bougie[])),
    ]);
    quotidien[ind.symbole] = d;
    const regle = stats?.indices[ind.symbole]?.choisie ?? REGLES_PAR_DEFAUT[ind.symbole];
    const plan = ferme ? undefined : publie?.indices[ind.symbole] ?? preparer(ind, date, d, h, regle) ?? undefined;
    return resumer(ind, maintenant, h, d, plan);
  }));
  const st: Record<string, StatsRegle | undefined> = {};
  for (const ind of INDICES) {
    const s = stats?.indices[ind.symbole];
    st[ind.symbole] = s?.regles[s.choisie];
  }
  return { maintenant, resumes, quotidien, stats: st, debutTest: stats?.debut, erreurs };
}
