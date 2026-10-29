import { describe, expect, it } from 'vitest';
import { tableau } from './tableau';

describe('tableau de bord', () => {
  it('réunit intraday et swing, dans l’ordre des dates', () => {
    const t = tableau(
      [
        { date: '2026-10-07', indice: 'DAX 40', pts: 0, euros: 0, statut: 'non déclenché' },
        { date: '2026-10-07', indice: 'Nasdaq 100', pts: -94.6, euros: -47.3, statut: 'perdu' },
        { date: '2026-10-08', indice: 'Nasdaq 100', pts: 277, euros: 138.5, statut: 'gagné' },
      ],
      [
        { date_signal: '2026-10-02', date_sortie: '2026-10-08', nom: 'Caterpillar', symbole: 'CAT', statut: 'échec', r: -1, prix_entree: 843.6, prix_sortie: 798.4, sens: 1 },
        { date_signal: '2026-10-14', date_sortie: '', symbole: 'COST', statut: 'ouvert', r: NaN, prix_entree: NaN, prix_sortie: NaN, sens: 1 },
      ],
      30,
    );
    expect(t.trades.map((x) => x.nom)).toEqual(['Caterpillar', 'Nasdaq 100', 'Nasdaq 100']);
    expect(t.cumul).toEqual([-30, -77.3, 61.2]);
    expect(t.totalEur).toBeCloseTo(61.2);
    expect(t.gainsEur).toBeCloseTo(138.5);
    expect(t.pertesEur).toBeCloseTo(-77.3);
    expect([t.gagnes, t.perdus, t.enCours]).toEqual([1, 2, 1]);
    expect(t.parType.swing).toEqual({ trades: 1, gagnes: 0, totalEur: -30 });
    expect(t.trades[0].pts).toBeCloseTo(-45.2);
  });
});
