/**
 * Charge tout l'écran : cours Yahoo, plan du jour (celui d'IG publié à 8h45 s'il existe, sinon calculé
 * sur le téléphone avec la même règle), état de chaque indice. Lecture seule : aucun ordre passé.
 */
import { type Bougie, type Indice, INDICES, type PlanIndice, REGLES_PAR_DEFAUT, type Resume, type Swing, analyserSwing, finSeance, paris, preparer, resumer, sma, weekEnd } from '../domain';
import type { LigneJournal, LignePlan, StatsDepot, StatsRegle } from '../adapters/depot';

export interface Sources {
  bougies(symbole: string, periode: string, intervalle: string): Promise<Bougie[]>;
  stats(): Promise<StatsDepot | null>;
  plan(date: string): Promise<{ indices: Record<string, PlanIndice> } | null>;
  journal(): Promise<LigneJournal[]>;
  planJournal(): Promise<LignePlan[]>;
}

export interface Marche {
  maintenant: number;
  resumes: Resume[];
  quotidien: Record<string, Bougie[]>;
  stats: Record<string, StatsRegle | undefined>;
  debutTest?: string;
  swing: Record<string, Swing | null>;
  /** lignes du journal swing du scanner, pour les 3 indices */
  journal: LigneJournal[];
  /** résultats réels du plan intraday */
  planJournal: LignePlan[];
  /** 1 € = eurUsd $ */
  eurUsd: number;
  erreurs: string[];
}

/** Bougies journalières terminées : celle du jour seulement après la fin de la séance. */
export function terminees(d: Bougie[], ind: Indice, maintenant: number): Bougie[] {
  const date = paris(maintenant).date;
  const fini = maintenant >= finSeance(ind, date);
  return d.filter((b) => paris(b.t).date < date || fini);
}

export async function charger(src: Sources, maintenant = Date.now()): Promise<Marche> {
  const date = paris(maintenant).date;
  const ferme = weekEnd(maintenant);
  const [stats, publie, journal, planJournal, fx] = await Promise.all([
    src.stats(), ferme ? null : src.plan(date), src.journal(), src.planJournal(),
    src.bougies('EURUSD=X', '5d', '1d').catch(() => [] as Bougie[]),
  ]);
  const erreurs: string[] = [];
  const quotidien: Record<string, Bougie[]> = {};
  const resumes = await Promise.all(INDICES.map(async (ind) => {
    const [d, h] = await Promise.all([
      src.bougies(ind.symbole, '2y', '1d').catch((e: Error) => (erreurs.push(e.message), [] as Bougie[])),
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
  // Filtre de marché du scanner : S&P 500 au-dessus de sa moyenne 200 jours = achats seulement, sinon ventes seulement.
  const spx = terminees(quotidien['^GSPC'] ?? [], INDICES[2], maintenant).map((b) => b.c);
  const m200 = sma(spx, 200)[spx.length - 1];
  const marcheHaussier = m200 === null || m200 === undefined ? null : spx[spx.length - 1] > m200;
  const swing: Record<string, Swing | null> = {};
  for (const ind of INDICES) {
    const d = terminees(quotidien[ind.symbole], ind, maintenant);
    swing[ind.symbole] = d.length ? analyserSwing(d, paris(d[d.length - 1].t).date, marcheHaussier) : null;
  }
  const symboles = new Set(INDICES.map((i) => i.symbole));
  return { maintenant, resumes, quotidien, stats: st, debutTest: stats?.debut, swing, journal: journal.filter((l) => symboles.has(l.symbole)), planJournal,
    eurUsd: fx.length ? fx[fx.length - 1].c : 1.08, erreurs };
}
