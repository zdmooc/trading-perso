import { describe, expect, it } from 'vitest';
import { INDICES } from './plan';
import { taille } from './taille';
import { bilanPerso, euros, points, type TradePerso } from './journalPerso';

describe('taille de position', () => {
  it('IG : contrats pour le risque voulu, jamais sous le minimum', () => {
    const t = taille(INDICES[0], 30, 75, 24000, 1.08);
    expect(t.ig).toBe(0.5); // 30 / 75 = 0,4 < minimum 0,5
    expect(t.igRisque).toBeCloseTo(37.5);
    expect(taille(INDICES[0], 60, 75, 24000, 1.08).ig).toBe(0.8);
  });

  it('eToro : unités en dollars pour les indices américains', () => {
    const t = taille(INDICES[2], 30, 20, 7000, 1.08);
    expect(t.etoro).toBe(1.62); // 30 € × 1,08 / 20 pts
    expect(t.etoroRisque).toBeCloseTo(30, 0);
    expect(t.etoroSpread).toBeCloseTo((2 * 1.62 * 7000 * 0.007) / 100 / 1.08, 6);
  });
});

describe('mes trades', () => {
  const base: TradePerso = { id: 'a', quand: 0, symbole: '^GDAXI', type: 'intraday', courtier: 'IG', sens: -1,
    entree: 24000, stop: 24075, objectif: 23775, quantite: 0.5, eurParPoint: 0.5 };

  it('points et euros, ouverts au cours du moment ou clôturés', () => {
    expect(points(base, 23950)).toBe(50);
    expect(euros(base, 23950)).toBe(25);
    expect(points(base)).toBeNull();
  });

  it('bilan des trades clôturés par type', () => {
    const b = bilanPerso([{ ...base, sortie: 23775 }, { ...base, id: 'b', sortie: 24075 }, { ...base, id: 'c', type: 'swing', sortie: 1 }], 'intraday');
    expect(b).toMatchObject({ trades: 2, gagnes: 1, perdus: 1, totalPts: 150, totalEur: 75 });
  });
});
