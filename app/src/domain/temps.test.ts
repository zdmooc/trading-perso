import { describe, expect, it } from 'vitest';
import { depuisParis, paris } from './temps';
import { nombre, pts, variation } from './format';

describe('heure de Paris', () => {
  it('été : UTC+2, hiver : UTC+1, bascule le dernier dimanche d’octobre', () => {
    expect(paris(Date.parse('2026-10-24T07:00:00Z'))).toMatchObject({ date: '2026-10-24', heure: 9 });
    expect(paris(Date.parse('2026-10-26T07:00:00Z'))).toMatchObject({ date: '2026-10-26', heure: 8 });
    expect(paris(Date.parse('2026-03-29T00:59:00Z')).heure).toBe(1);
    expect(paris(Date.parse('2026-03-29T01:00:00Z')).heure).toBe(3);
  });

  it('depuisParis est l’inverse de paris', () => {
    expect(new Date(depuisParis('2026-10-28', 15, 30)).toISOString()).toBe('2026-10-28T14:30:00.000Z');
    expect(new Date(depuisParis('2026-07-01', 9)).toISOString()).toBe('2026-07-01T07:00:00.000Z');
  });
});

describe('format', () => {
  it('milliers, signe, points à côté du pourcentage', () => {
    expect(nombre(24816.45, 0)).toBe('24 816');
    expect(nombre(-1.234, 1)).toBe('−1,2');
    expect(pts(-298.8)).toBe('−299 pts');
    expect(variation(-298.8, 24816)).toBe('−299 pts (−1,2 %)');
  });
});

describe('heures américaines', () => {
  it('une heure plus tôt quand Paris et New York ne changent pas d’heure le même jour', async () => {
    const { avanceUs } = await import('./temps');
    expect(avanceUs(Date.parse('2026-10-28T15:00:00Z'))).toBe(1);
    expect(avanceUs(Date.parse('2026-11-03T15:00:00Z'))).toBe(0);
    expect(avanceUs(Date.parse('2026-03-10T15:00:00Z'))).toBe(1);
    expect(avanceUs(Date.parse('2026-07-01T15:00:00Z'))).toBe(0);
  });

  it('fin de séance et fenêtre du jour', async () => {
    const { INDICES, fenetre, finSeance } = await import('./plan');
    expect(new Date(finSeance(INDICES[1], '2026-10-28')).toISOString()).toBe('2026-10-28T20:00:00.000Z');
    expect(new Date(finSeance(INDICES[1], '2026-11-03')).toISOString()).toBe('2026-11-03T21:00:00.000Z');
    expect(fenetre(INDICES[1], '2026-10-28')).toContain('14h30');
    expect(fenetre(INDICES[0], '2026-10-28')).toBe(INDICES[0].fenetre);
  });
});
