import { describe, expect, it } from 'vitest';
import { lireCompte, pointsPosition, recosEtoro } from './etoro';
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
