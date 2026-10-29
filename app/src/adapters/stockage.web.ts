/** Version web (aperçu) du stockage : localStorage du navigateur. */
import type { TradePerso } from '../domain';
import type { Reglages } from './stockage';

function lire<T>(cle: string, defaut: T): T {
  try {
    const v = globalThis.localStorage?.getItem(cle);
    return v ? (JSON.parse(v) as T) : defaut;
  } catch {
    return defaut;
  }
}

function ecrire(cle: string, v: unknown): void {
  try {
    globalThis.localStorage?.setItem(cle, JSON.stringify(v));
  } catch {
    // aperçu seulement
  }
}

export type { Reglages };
export const lireReglages = (): Reglages => ({ risqueEur: 30, alertes: true, ...lire<Partial<Reglages>>('reglages', {}) });
export const ecrireReglages = (r: Reglages) => ecrire('reglages', r);
export const lireTrades = (): TradePerso[] => lire<TradePerso[]>('trades', []);
export const ecrireTrades = (t: TradePerso[]) => ecrire('trades', t);
export const lireAlertesVues = () => new Set<string>();
export const ajouterAlertesVues = (_cles: string[]) => undefined;
