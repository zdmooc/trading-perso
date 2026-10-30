/** Lecture du compte eToro et niveaux du plan recalés sur le cours eToro. Lecture seule : rien ici ne passe d'ordre. */
import { type Resume } from './marche';
import { type Swing } from './swing';
import { INSTRUMENTS, taille } from './taille';

export interface PositionEtoro {
  id: number;
  instrumentId: number;
  achat: boolean;
  unites: number;
  ouverture: number;
  actuel: number | null;
  /** gain ou perte latent, en dollars (devise du compte) */
  pnlUsd: number | null;
  levier: number;
  stop: number | null;
  objectif: number | null;
  depuis: string;
}

export interface CompteEtoro {
  /** solde disponible, en dollars */
  creditUsd: number | null;
  pnlUsd: number | null;
  positions: PositionEtoro[];
}

type Brut = Record<string, unknown>;

/** L'API eToro n'écrit pas toujours les clés avec la même casse (positionId / positionID). */
function champ(o: Brut, ...noms: string[]): unknown {
  for (const n of noms) {
    const k = Object.keys(o).find((x) => x.toLowerCase() === n.toLowerCase());
    if (k !== undefined && o[k] !== null && o[k] !== undefined) return o[k];
  }
  return undefined;
}
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

/** Sans stop ni objectif, eToro garde des niveaux factices très loin du prix (0, ou 10 fois l'entrée) : on les ignore. */
function niveau(v: number | null, ouverture: number): number | null {
  return v === null || v <= 0 || (ouverture > 0 && (v > ouverture * 5 || v < ouverture / 5)) ? null : v;
}

export function lireCompte(rep: unknown): CompteEtoro {
  const cp = ((rep as Brut)?.clientPortfolio ?? {}) as Brut;
  const positions = ((champ(cp, 'positions') as Brut[] | undefined) ?? []).map((p): PositionEtoro => {
    const u = (champ(p, 'unrealizedPnL') ?? {}) as Brut;
    const ouverture = num(champ(p, 'openRate')) ?? 0;
    return {
      id: num(champ(p, 'positionId')) ?? 0,
      instrumentId: num(champ(p, 'instrumentId')) ?? 0,
      achat: champ(p, 'isBuy') !== false,
      unites: num(champ(p, 'units')) ?? 0,
      ouverture,
      actuel: num(champ(u, 'closeRate')) ?? num(champ(p, 'closeRate')),
      pnlUsd: num(champ(u, 'pnL')) ?? num(champ(p, 'pnL')),
      levier: num(champ(p, 'leverage')) ?? 1,
      stop: champ(p, 'isNoStopLoss') === true ? null : niveau(num(champ(p, 'stopLossRate')), ouverture),
      objectif: champ(p, 'isNoTakeProfit') === true ? null : niveau(num(champ(p, 'takeProfitRate')), ouverture),
      depuis: String(champ(p, 'openDateTime') ?? '').slice(0, 10),
    };
  });
  const pnl = num(champ(cp, 'unrealizedPnL'));
  return {
    creditUsd: num(champ(cp, 'credit')),
    pnlUsd: pnl ?? (positions.some((p) => p.pnlUsd !== null) ? positions.reduce((a, p) => a + (p.pnlUsd ?? 0), 0) : null),
    positions,
  };
}

/** Points gagnés ou perdus par une position, au cours actuel. */
export function pointsPosition(p: PositionEtoro): number | null {
  return p.actuel === null ? null : (p.achat ? 1 : -1) * (p.actuel - p.ouverture);
}

export interface Cotation {
  bid: number;
  ask: number;
}

export interface RecoEtoro {
  symbole: string;
  type: 'intraday' | 'swing';
  sens: 1 | -1;
  /** niveaux recalés sur le cours eToro */
  entree: number;
  stop: number;
  objectif: number;
  /** cours eToro moins cours de l'app (Yahoo), en points */
  decalage: number;
  spread: number;
  unites: number;
  risqueEur: number;
  gainEur: number;
  /** ce qu'il faut faire : « ordre à placer », « en position », « à l'ouverture » */
  quand: string;
  regle?: string;
}

/**
 * Recommandations d'achat et de vente du plan (intraday) et du scanner (swing), en instruments eToro.
 * Les niveaux sont décalés de l'écart entre le cours eToro et le cours de l'app.
 */
export function recosEtoro(resumes: Resume[], swing: Record<string, Swing | null>, cotes: Record<string, Cotation>,
  risqueEur: number, eurUsd: number): RecoEtoro[] {
  const out: RecoEtoro[] = [];
  for (const r of resumes) {
    const c = cotes[INSTRUMENTS[r.indice.symbole]?.etoro ?? ''];
    if (!c) continue;
    const milieu = (c.bid + c.ask) / 2;
    const ajoute = (type: RecoEtoro['type'], sens: 1 | -1, entree: number, stop: number, objectif: number, reference: number | undefined, quand: string, regle?: string) => {
      // Plus de 1 % d'écart : ce n'est pas le même sous-jacent (ou cours figé), on ne recale pas.
      const brut = reference === undefined ? 0 : milieu - reference;
      const d = Math.abs(brut) > 0.01 * milieu ? 0 : brut;
      const t = taille(r.indice, risqueEur, Math.abs(entree - stop), entree + d, eurUsd);
      out.push({
        symbole: r.indice.symbole, type, sens, entree: entree + d, stop: stop + d, objectif: objectif + d, decalage: d,
        spread: c.ask - c.bid, unites: t.etoro, risqueEur: t.etoroRisque, gainEur: t.etoroEurParPoint * Math.abs(objectif - entree), quand, regle,
      });
    };
    if (r.etat.type === 'attendre') for (const o of r.ordres) ajoute('intraday', o.sens, o.niveau, o.stop, o.objectif, r.prix, 'ordre à placer');
    if (r.etat.type === 'position') {
      const t = r.etat.trade;
      ajoute('intraday', t.sens, t.entree, t.stop, t.objectif, r.prix, 'déjà déclenché aujourd’hui');
    }
    const s = swing[r.indice.symbole];
    for (const sig of s?.signaux ?? []) ajoute('swing', sig.regle.sens, sig.cours, sig.stop, sig.objectif, r.prix, 'à l’ouverture de la prochaine séance', sig.regle.nom);
  }
  return out;
}

/** Un trade réel sur eToro (position ouverte ou fermée). */
export interface TradeReel {
  instrumentId: number;
  achat: boolean;
  ouverture: number;
  /** date d'ouverture, AAAA-MM-JJ */
  date: string;
}

/** Historique eToro (/trade/history) : la liste peut être à la racine ou sous une clé. */
export function lireHistorique(rep: unknown): TradeReel[] {
  const liste = Array.isArray(rep) ? rep
    : (Object.values((rep ?? {}) as Brut).find(Array.isArray) as unknown[] | undefined) ?? [];
  return (liste as Brut[]).map((p) => ({
    instrumentId: num(champ(p, 'instrumentId')) ?? 0,
    achat: champ(p, 'isBuy') !== false,
    ouverture: num(champ(p, 'openRate')) ?? 0,
    date: String(champ(p, 'openTimestamp', 'openDateTime', 'openDate') ?? '').slice(0, 10),
  })).filter((t) => t.instrumentId && t.ouverture && t.date);
}

export interface EcartReel {
  date: string;
  indice: string;
  sens: 1 | -1;
  plan: number;
  reel: number;
  /** points perdus par rapport à l'entrée du plan (négatif : meilleur prix que le plan) */
  ecart: number;
}

/**
 * Entrées réelles eToro comparées aux entrées du plan intraday : même jour, même indice, même sens.
 * `indices` donne le nom de l'indice du plan (« DAX 40 ») pour chaque instrument eToro.
 */
export function ecartsReels(trades: TradeReel[], plan: { date: string; indice: string; sens: string; entree: number }[],
  indices: Record<number, string>): EcartReel[] {
  const out: EcartReel[] = [];
  const vus = new Set<string>();
  for (const t of trades) {
    const nom = indices[t.instrumentId];
    if (!nom) continue;
    const l = plan.find((x) => x.date === t.date && x.indice === nom && x.sens === (t.achat ? 'achat' : 'vente') && Number.isFinite(x.entree));
    const cle = `${t.date}|${nom}|${t.ouverture}`;
    if (!l || vus.has(cle)) continue;
    vus.add(cle);
    const sens = t.achat ? 1 : -1;
    out.push({ date: t.date, indice: nom, sens, plan: l.entree, reel: t.ouverture, ecart: sens * (t.ouverture - l.entree) });
  }
  return out.sort((a, b) => a.date.localeCompare(b.date));
}
