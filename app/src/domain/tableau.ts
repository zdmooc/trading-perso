/** Tableau de bord des signaux suivis : gains, pertes et total, intraday et swing réunis. */

export interface TradeSuivi {
  date: string;
  type: 'intraday' | 'swing';
  nom: string;
  eur: number;
  /** points pour l'intraday, écart de prix pour le swing */
  pts: number;
}

export interface Tableau {
  trades: TradeSuivi[];
  /** total cumulé après chaque trade, dans l'ordre des trades */
  cumul: number[];
  totalEur: number;
  gainsEur: number;
  pertesEur: number;
  gagnes: number;
  perdus: number;
  enCours: number;
  parType: Record<'intraday' | 'swing', { trades: number; gagnes: number; totalEur: number }>;
}

/**
 * Intraday : résultats réels du plan, en taille du plan.
 * Swing : résultat en risques (r) du scanner, converti au risque choisi dans les réglages.
 */
export function tableau(
  plan: { date: string; indice: string; pts: number; euros: number; statut: string }[],
  swing: { date_signal: string; date_sortie: string; nom?: string; symbole: string; statut: string; r: number; prix_entree: number; prix_sortie: number; sens: number }[],
  risqueEur: number,
): Tableau {
  const trades: TradeSuivi[] = [
    ...plan.filter((l) => l.statut === 'gagné' || l.statut === 'perdu')
      .map((l) => ({ date: l.date, type: 'intraday' as const, nom: l.indice, eur: l.euros, pts: l.pts })),
    ...swing.filter((l) => ['succès', 'échec', 'neutre'].includes(l.statut) && Number.isFinite(l.r))
      .map((l) => ({ date: l.date_signal, type: 'swing' as const, nom: l.nom || l.symbole, eur: l.r * risqueEur, pts: l.sens * (l.prix_sortie - l.prix_entree) })),
  ].sort((a, b) => a.date.localeCompare(b.date) || a.type.localeCompare(b.type));
  let s = 0;
  const cumul = trades.map((t) => (s += t.eur));
  const parType = (type: 'intraday' | 'swing') => {
    const l = trades.filter((t) => t.type === type);
    return { trades: l.length, gagnes: l.filter((t) => t.eur > 0).length, totalEur: l.reduce((a, t) => a + t.eur, 0) };
  };
  const gains = trades.filter((t) => t.eur > 0);
  return {
    trades, cumul, totalEur: s,
    gainsEur: gains.reduce((a, t) => a + t.eur, 0),
    pertesEur: trades.filter((t) => t.eur <= 0).reduce((a, t) => a + t.eur, 0),
    gagnes: gains.length, perdus: trades.length - gains.length,
    enCours: swing.filter((l) => l.statut === 'ouvert').length,
    parType: { intraday: parType('intraday'), swing: parType('swing') },
  };
}
