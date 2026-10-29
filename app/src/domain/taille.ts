/**
 * Taille de position pour un risque donné en euros (portage de src/tradeperso/execution.py).
 * IG : contrats à 1 €/point (minimum = taille du plan). eToro : unités de CFD, 1 point = 1 unité de la devise de l'indice.
 */
import type { Indice } from './plan';

/** Spread eToro en % du prix (config.toml, instruments.*.etoro_spread_pct). */
const SPREAD_ETORO_PCT = 0.007;

export const INSTRUMENTS: Record<string, { ig: string; etoro: string; devise: 'EUR' | 'USD' }> = {
  '^GDAXI': { ig: 'Allemagne 40', etoro: 'GER40', devise: 'EUR' },
  '^NDX': { ig: 'US Tech 100', etoro: 'NSDQ100', devise: 'USD' },
  '^GSPC': { ig: 'US 500', etoro: 'SPX500', devise: 'USD' },
};

export interface Taille {
  /** contrats IG (arrondis au centième, jamais sous le minimum) */
  ig: number;
  igMinimum: number;
  /** risque réel en € avec la taille IG retenue */
  igRisque: number;
  igSpread: number;
  /** unités eToro (arrondies au centième) */
  etoro: number;
  etoroRisque: number;
  etoroSpread: number;
  /** euros gagnés ou perdus par point, eToro */
  etoroEurParPoint: number;
}

const arrondi = (x: number) => Math.max(0, Math.floor(x * 100 + 1e-9) / 100);

/**
 * @param ecart distance entrée-stop en points
 * @param eurUsd cours EUR/USD (1 € = eurUsd $)
 */
export function taille(ind: Indice, risqueEur: number, ecart: number, entree: number, eurUsd: number): Taille {
  const fx = INSTRUMENTS[ind.symbole]?.devise === 'USD' ? eurUsd : 1;
  const ig = Math.max(ind.taille, arrondi(risqueEur / ecart));
  const etoro = arrondi((risqueEur * fx) / ecart);
  return {
    ig, igMinimum: ind.taille, igRisque: ig * ecart, igSpread: ig * ind.spread,
    etoro, etoroRisque: (etoro * ecart) / fx, etoroSpread: (2 * etoro * entree * SPREAD_ETORO_PCT) / 100 / fx,
    etoroEurParPoint: etoro / fx,
  };
}
