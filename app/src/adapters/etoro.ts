/**
 * API publique eToro, EN LECTURE SEULE : ce module ne fait que des GET.
 * Aucune route d'ordre, de clôture ou de modification n'est appelée, et la clé à créer sur eToro est une clé « lecture ».
 * Les clés restent sur le téléphone.
 */
import { type CompteEtoro, type Cotation, type TradeReel, INDICES, INSTRUMENTS, lireCompte, lireHistorique } from '../domain';

const BASE = 'https://public-api.etoro.com';

export interface ClesEtoro {
  /** clé publique (x-api-key) */
  api: string;
  /** clé utilisateur (x-user-key) */
  user: string;
}

const uuid = () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (ch) => {
  const r = (Math.random() * 16) | 0;
  return (ch === 'x' ? r : (r & 0x3) | 0x8).toString(16);
});

async function lire(cles: ClesEtoro, chemin: string): Promise<unknown> {
  const r = await fetch(BASE + chemin, {
    method: 'GET',
    headers: { 'x-api-key': cles.api.trim(), 'x-user-key': cles.user.trim(), 'x-request-id': uuid(), accept: 'application/json' },
  });
  if (r.status === 401 || r.status === 403) throw new Error('clés refusées par eToro (vérifie-les dans les réglages)');
  if (r.status === 429) throw new Error('trop de demandes, réessaie dans une minute');
  if (r.status === 204) return null;
  if (!r.ok) throw new Error(`eToro a répondu ${r.status}`);
  return r.json();
}

interface Instrument {
  id: number;
  symbole: string;
  nom: string;
}

async function instruments(cles: ClesEtoro, q: string): Promise<Instrument[]> {
  const rep = (await lire(cles, `/api/v2/market-data/instruments?${q}`)) as { results?: { instrumentId: number; symbol: string; displayName: string }[] } | null;
  return (rep?.results ?? []).map((x) => ({ id: x.instrumentId, symbole: x.symbol, nom: x.displayName }));
}

async function cotations(cles: ClesEtoro, ids: number[]): Promise<Record<number, Cotation>> {
  if (!ids.length) return {};
  const rep = (await lire(cles, `/api/v2/market-data/rates?instrumentIds=${ids.join(',')}`)) as { results?: { instrumentId: number; bid: number | null; ask: number | null }[] } | null;
  const out: Record<number, Cotation> = {};
  for (const x of rep?.results ?? []) if (x.bid !== null && x.ask !== null) out[x.instrumentId] = { bid: x.bid, ask: x.ask };
  return out;
}

export interface DonneesEtoro {
  compte: CompteEtoro;
  /** nom de chaque instrument du compte et des suggestions */
  noms: Record<number, string>;
  /** cotations des indices du plan, par symbole eToro (GER40…) */
  indices: Record<string, Cotation>;
  /** suggestions personnalisées d'eToro (des instruments, pas des signaux d'achat) */
  suggestions: { id: number; nom: string; cote?: Cotation }[];
  /** trades des 60 derniers jours (fermés et ouverts), pour comparer les prix réels au plan */
  trades: TradeReel[];
  /** nom de l'indice du plan (« DAX 40 ») de chaque instrument eToro des indices */
  idsIndices: Record<number, string>;
}

export async function chargerEtoro(cles: ClesEtoro): Promise<DonneesEtoro> {
  const symboles = Object.values(INSTRUMENTS).map((i) => i.etoro);
  const depuis = new Date(Date.now() - 60 * 86_400_000).toISOString().slice(0, 10);
  const [pnl, idx, reco, histo] = await Promise.all([
    lire(cles, '/api/v1/trading/info/real/pnl'),
    instruments(cles, `symbols=${symboles.join(',')}`),
    lire(cles, '/api/v1/market-recommendations/10').catch(() => null),
    lire(cles, `/api/v1/trading/info/trade/history?minDate=${depuis}`).catch(() => null),
  ]);
  const compte = lireCompte(pnl);
  const recoIds = ((reco as { Recommendations?: number[] } | null)?.Recommendations ?? []).slice(0, 10);
  const autres = [...new Set([...compte.positions.map((p) => p.instrumentId), ...recoIds])].filter((id) => !idx.some((i) => i.id === id));
  const [infos, cotes] = await Promise.all([
    autres.length ? instruments(cles, `instrumentsIds=${autres.join(',')}`) : Promise.resolve([]),
    cotations(cles, [...idx.map((i) => i.id), ...recoIds]),
  ]);
  const noms: Record<number, string> = {};
  for (const i of [...idx, ...infos]) noms[i.id] = i.nom || i.symbole;
  const indices: Record<string, Cotation> = {};
  for (const i of idx) if (cotes[i.id]) indices[i.symbole.toUpperCase()] = cotes[i.id];
  const idsIndices: Record<number, string> = {};
  for (const i of idx) {
    const s = Object.keys(INSTRUMENTS).find((k) => INSTRUMENTS[k].etoro === i.symbole.toUpperCase());
    const nom = INDICES.find((x) => x.symbole === s)?.nom;
    if (nom) idsIndices[i.id] = nom;
  }
  const trades = [...lireHistorique(histo), ...compte.positions.map((p) => ({ instrumentId: p.instrumentId, achat: p.achat, ouverture: p.ouverture, date: p.depuis }))];
  return { compte, noms, indices, suggestions: recoIds.map((id) => ({ id, nom: noms[id] ?? `#${id}`, cote: cotes[id] })), trades, idsIndices };
}
