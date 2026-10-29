/** Données gardées sur le téléphone (SQLite, jamais envoyées) : réglages, mes trades, alertes déjà vues. */
import Storage from 'expo-sqlite/kv-store';
import type { TradePerso } from '../domain';

function lire<T>(cle: string, defaut: T): T {
  try {
    const v = Storage.getItemSync(cle);
    return v === null ? defaut : (JSON.parse(v) as T);
  } catch {
    return defaut;
  }
}

function ecrire(cle: string, v: unknown): void {
  try {
    Storage.setItemSync(cle, JSON.stringify(v));
  } catch (e) {
    console.warn('stockage', cle, e);
  }
}

export interface Reglages {
  /** risque par trade en euros, pour le calcul de la taille */
  risqueEur: number;
  alertes: boolean;
}

const REGLAGES: Reglages = { risqueEur: 30, alertes: true };

export const lireReglages = (): Reglages => ({ ...REGLAGES, ...lire<Partial<Reglages>>('reglages', {}) });
export const ecrireReglages = (r: Reglages) => ecrire('reglages', r);

export const lireTrades = (): TradePerso[] => lire<TradePerso[]>('trades', []);
export const ecrireTrades = (t: TradePerso[]) => ecrire('trades', t);

/** Clés des alertes déjà envoyées (préfixées par la date) : on ne garde que les 3 derniers jours. */
export function lireAlertesVues(): Set<string> {
  return new Set(lire<string[]>('alertes-vues', []));
}

export function ajouterAlertesVues(cles: string[]): void {
  const limite = new Date(Date.now() - 3 * 86_400_000).toISOString().slice(0, 10);
  const garde = [...lireAlertesVues(), ...cles].filter((k) => k.slice(0, 10) >= limite);
  ecrire('alertes-vues', [...new Set(garde)]);
}

/** Clés de l'API eToro (lecture seule), saisies dans l'onglet eToro. */
export const lireClesEtoro = (): { api: string; user: string } | null => lire<{ api: string; user: string } | null>('etoro-cles', null);
export const ecrireClesEtoro = (c: { api: string; user: string } | null) => ecrire('etoro-cles', c);
