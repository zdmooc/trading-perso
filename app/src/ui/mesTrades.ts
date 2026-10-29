import { useCallback, useState } from 'react';
import type { TradePerso } from '../domain';
import { ecrireReglages, ecrireTrades, lireReglages, lireTrades, type Reglages } from '../adapters/stockage';

/** Mes trades et mes réglages, gardés sur le téléphone. */
export function useMesDonnees() {
  const [trades, setTrades] = useState<TradePerso[]>(lireTrades);
  const [reglages, setReglagesEtat] = useState<Reglages>(lireReglages);
  const enregistrer = useCallback((t: TradePerso[]) => {
    ecrireTrades(t);
    setTrades(t);
  }, []);
  return {
    trades,
    reglages,
    setReglages: (r: Reglages) => {
      ecrireReglages(r);
      setReglagesEtat(r);
    },
    ajouter: (t: TradePerso) => enregistrer([...trades, t]),
    cloturer: (id: string, sortie: number) => enregistrer(trades.map((t) => (t.id === id ? { ...t, sortie, quandSortie: Date.now() } : t))),
    supprimer: (id: string) => enregistrer(trades.filter((t) => t.id !== id)),
  };
}

export type MesDonnees = ReturnType<typeof useMesDonnees>;

/** Nombre saisi à la française (« 24 583,5 »). */
export function lireNombre(texte: string): number | null {
  const n = Number(texte.replace(/[\s ]/g, '').replace(',', '.'));
  return texte.trim() && Number.isFinite(n) ? n : null;
}
