/** Chiffres d'un indice pour l'écran : cours, plan, état du trade, contexte (portage de horaire.resume). */
import { atr, rsi, sma } from './indicateurs';
import { type Bougie, type Indice, type Ordre, type PlanIndice, type Trade, RATIO, pivotsSemaine, rejouer, seances } from './plan';
import { dateFr, depuisParis, hhmm, paris } from './temps';

export type Etat =
  | { type: 'pas-de-plan' }
  | { type: 'attendre' }
  | { type: 'position'; trade: Trade }
  | { type: 'termine'; trade: Trade }
  | { type: 'rien'; raison: string };

export interface OrdreVu extends Ordre {
  stop: number;
  objectif: number;
  /** niveau moins cours, en points */
  distance: number | null;
}

export interface Resume {
  indice: Indice;
  jour: Bougie[];
  /** bougies du graphique : aujourd'hui, sinon la dernière journée connue */
  graphe: Bougie[];
  prix?: number;
  heure?: string;
  haut?: number;
  bas?: number;
  /** écart avec la clôture de la veille du plan, en points */
  ecart?: number;
  plan?: PlanIndice;
  ordres: OrdreVu[];
  etat: Etat;
  /** message court sous le nom quand il n'y a encore rien à jouer */
  info?: string;
  contexte?: { rsi: number; mm20: number; mm50: number; atr: number; tendance: string };
  pivots: Record<string, number>;
}

export function resumer(ind: Indice, maintenant: number, intraday: Bougie[], quotidien: Bougie[], plan: PlanIndice | undefined): Resume {
  const p = paris(maintenant);
  const ses = seances(intraday, ind).get(p.date) ?? [];
  const jour = intraday.filter((b) => paris(b.t).date === p.date);
  const derniere = intraday.length ? paris(intraday[intraday.length - 1].t).date : '';
  const graphe = jour.length ? jour : intraday.filter((b) => paris(b.t).date === derniere);
  const r: Resume = { indice: ind, jour, graphe, plan, ordres: [], etat: { type: 'pas-de-plan' }, pivots: pivotsSemaine(quotidien, p.date) };
  if (intraday.length) {
    // Sans cours aujourd'hui (week-end, avant l'ouverture) : dernier cours connu, avec sa date.
    const der = intraday[intraday.length - 1];
    const pd = paris(der.t);
    r.prix = der.c;
    r.heure = (jour.length ? '' : `${dateFr(pd.date)} `) + hhmm(pd);
  }
  if (jour.length) {
    r.haut = Math.max(...jour.map((b) => b.h));
    r.bas = Math.min(...jour.map((b) => b.l));
  }
  if (plan) {
    if (r.prix !== undefined && jour.length) r.ecart = r.prix - plan.cloture;
    r.ordres = plan.ordres.map((o) => ({
      ...o, stop: o.niveau - o.sens * o.risque, objectif: o.niveau + o.sens * RATIO * o.risque,
      distance: r.prix === undefined || !jour.length ? null : o.niveau - r.prix,
    }));
    const fini = maintenant >= depuisParis(p.date, ind.heures[1] + 1);
    const t = ses.length ? rejouer(ses, plan.ordres, ind.finEntree, ind.spread, fini) : null;
    if (t) r.etat = t.motif === 'en cours' ? { type: 'position', trade: t } : { type: 'termine', trade: t };
    else if (p.heure > ind.finEntree || fini) r.etat = { type: 'rien', raison: 'aucun niveau touché avant l’heure limite' };
    else r.etat = { type: 'attendre' };
    if (!ses.length && !fini) {
      r.info = maintenant < depuisParis(p.date, ind.heures[0], ind.debutMin) ? 'séance pas encore ouverte' : 'cours pas encore disponibles';
    }
  }
  if (quotidien.length > 60) {
    const c = quotidien.map((b) => b.c);
    const n = c.length - 1;
    const mm20 = sma(c, 20)[n] as number, mm50 = sma(c, 50)[n] as number;
    r.contexte = {
      rsi: rsi(c)[n] as number, mm20, mm50, atr: atr(quotidien)[n] as number,
      tendance: c[n] > mm20 && mm20 > mm50 ? 'haussière' : c[n] < mm20 && mm20 < mm50 ? 'baissière' : 'sans direction nette',
    };
  }
  return r;
}

export function weekEnd(maintenant: number): boolean {
  const j = paris(maintenant).jour;
  return j === 0 || j === 6;
}
