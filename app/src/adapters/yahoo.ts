/** Cours Yahoo Finance (gratuits, sans clé). Les bougies incomplètes (valeurs nulles) sont ignorées. */
import type { Bougie } from '../domain';

interface ReponseYahoo {
  chart: {
    result?: {
      timestamp?: number[];
      indicators: { quote: { open: (number | null)[]; high: (number | null)[]; low: (number | null)[]; close: (number | null)[] }[] };
    }[];
    error?: { description?: string } | null;
  };
}

export function lireYahoo(j: ReponseYahoo): Bougie[] {
  const r = j.chart.result?.[0];
  if (!r?.timestamp) throw new Error(j.chart.error?.description ?? 'réponse Yahoo vide');
  const q = r.indicators.quote[0];
  const out: Bougie[] = [];
  r.timestamp.forEach((t, i) => {
    const [o, h, l, c] = [q.open[i], q.high[i], q.low[i], q.close[i]];
    if (o != null && h != null && l != null && c != null) out.push({ t: t * 1000, o, h, l, c });
  });
  return out;
}

export async function bougiesYahoo(symbole: string, periode: string, intervalle: string): Promise<Bougie[]> {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbole)}?range=${periode}&interval=${intervalle}`;
  const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
  if (!r.ok) throw new Error(`Yahoo ${symbole} : erreur ${r.status}`);
  return lireYahoo((await r.json()) as ReponseYahoo);
}
