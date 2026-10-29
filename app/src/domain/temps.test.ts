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
