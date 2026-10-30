import { describe, expect, it } from 'vitest';
import { ecartsReels, lireCompte, lireHistorique, pointsPosition, recosEtoro } from './etoro';
import { INDICES } from './plan';
import type { Resume } from './marche';

describe('compte eToro', () => {
  it('lit les positions quelle que soit la casse des clés', () => {
    const c = lireCompte({ clientPortfolio: { credit: 1200, unrealizedPnL: 15, positions: [
      { positionID: 7, instrumentID: 32, isBuy: false, units: 2, openRate: 24000, leverage: 5, stopLossRate: 24100, isNoTakeProfit: true,
        openDateTime: '2026-10-20T08:00:00Z', unrealizedPnL: { pnL: 30, closeRate: 23985 } },
    ] } });
    expect(c.creditUsd).toBe(1200);
    expect(c.pnlUsd).toBe(15);
    expect(c.positions[0]).toMatchObject({ id: 7, instrumentId: 32, achat: false, unites: 2, actuel: 23985, pnlUsd: 30, stop: 24100, objectif: null, depuis: '2026-10-20' });
    expect(pointsPosition(c.positions[0])).toBe(15);
  });

  it('ignore les stops et objectifs factices d’eToro', () => {
    const c = lireCompte({ clientPortfolio: { positions: [{ positionId: 1, instrumentId: 100001, isBuy: true, units: 0.01, openRate: 1876, stopLossRate: 0.0001, takeProfitRate: 20633 }] } });
    expect(c.positions[0]).toMatchObject({ stop: null, objectif: null });
  });

  it('réponse vide : aucun plantage', () => {
    expect(lireCompte(null)).toEqual({ creditUsd: null, pnlUsd: null, positions: [] });
  });
});

describe('recommandations eToro', () => {
  it('recale les niveaux du plan sur le cours eToro', () => {
    const dax = INDICES[0];
    const r = {
      indice: dax, prix: 24000, ordres: [{ sens: 1, niveau: 24050, cote: 'haut', stop: 24000, objectif: 24200, distance: 50 }],
      etat: { type: 'attendre' },
    } as unknown as Resume;
    const [reco] = recosEtoro([r], {}, { GER40: { bid: 24009, ask: 24011 } }, 30, 1.08);
    expect(reco).toMatchObject({ type: 'intraday', sens: 1, entree: 24060, stop: 24010, objectif: 24210, decalage: 10, spread: 2, quand: 'ordre à placer' });
    expect(reco.unites).toBeCloseTo(0.6);
    expect(reco.risqueEur).toBeCloseTo(30);
    expect(reco.gainEur).toBeCloseTo(90);
  });

  it('ne recale pas quand le cours eToro est trop loin (plus de 1 %)', () => {
    const r = { indice: INDICES[0], prix: 24000, ordres: [{ sens: -1, niveau: 23950, cote: 'bas', stop: 24000, objectif: 23800, distance: -50 }], etat: { type: 'attendre' } } as unknown as Resume;
    expect(recosEtoro([r], {}, { GER40: { bid: 24500, ask: 24502 } }, 30, 1.08)[0]).toMatchObject({ entree: 23950, decalage: 0 });
  });
});

describe('écart entre le prix réel eToro et le plan', () => {
  const plan = [
    { date: '2026-10-20', indice: 'DAX 40', sens: 'achat', entree: 24000 },
    { date: '2026-10-21', indice: 'Nasdaq 100', sens: 'vente', entree: 25000 },
    { date: '2026-10-22', indice: 'DAX 40', sens: '', entree: NaN },
  ];
  const ids = { 32: 'DAX 40', 28: 'Nasdaq 100' };

  it('lit l’historique, à la racine ou sous une clé', () => {
    const t = { instrumentID: 32, isBuy: true, openRate: 24003, openTimestamp: '2026-10-20T08:15:00Z' };
    expect(lireHistorique([t])).toEqual([{ instrumentId: 32, achat: true, ouverture: 24003, date: '2026-10-20' }]);
    expect(lireHistorique({ trades: [t] })).toHaveLength(1);
    expect(lireHistorique(null)).toEqual([]);
  });

  it('même jour, même indice, même sens : écart en points, positif si le prix est moins bon', () => {
    const e = ecartsReels([
      { instrumentId: 32, achat: true, ouverture: 24003, date: '2026-10-20' },
      { instrumentId: 28, achat: false, ouverture: 25001, date: '2026-10-21' },
      { instrumentId: 28, achat: true, ouverture: 25001, date: '2026-10-21' },
      { instrumentId: 99, achat: true, ouverture: 10, date: '2026-10-20' },
    ], plan, ids);
    expect(e.map((x) => [x.indice, x.ecart])).toEqual([['DAX 40', 3], ['Nasdaq 100', -1]]);
  });
});
