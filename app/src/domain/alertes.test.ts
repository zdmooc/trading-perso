import { describe, expect, it } from 'vitest';
import { alertes } from './alertes';
import { resumer } from './marche';
import { type Bougie, INDICES, type PlanIndice } from './plan';

const dax = INDICES[0];
const plan: PlanIndice = { source: 'Yahoo', regle: 'cassure-0.25-aucun', veille: '2026-10-27', cloture: 24000,
  ordres: [{ sens: 1, niveau: 24100, cote: 'haut', risque: 50 }] };
const t9 = Date.parse('2026-10-28T08:00:00Z');
const b = (k: number, o: number, h: number, l: number, c: number): Bougie => ({ t: t9 + k * 1_800_000, o, h, l, c });

describe('alertes', () => {
  it('entrée proche, une seule fois', () => {
    const r = resumer(dax, t9 + 1_000_000, [b(0, 24050, 24090, 24040, 24085)], [], plan);
    const a = alertes([r], new Set());
    expect(a.map((x) => x.titre)).toEqual(['🇩🇪 DAX 40 : entrée proche']);
    expect(alertes([r], new Set(a.map((x) => x.cle)))).toEqual([]);
  });

  it('entrée touchée puis objectif atteint', () => {
    const r = resumer(dax, t9 + 3_600_000, [b(0, 24050, 24120, 24040, 24110), b(1, 24110, 24310, 24100, 24305)], [], plan);
    expect(alertes([r], new Set()).map((x) => x.titre)).toEqual(['🇩🇪 DAX 40 : entrée touchée', '🇩🇪 DAX 40 : objectif atteint ✅']);
  });
});
