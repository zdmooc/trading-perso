import { describe, expect, it } from 'vitest';
import { resumer } from './marche';
import { type Bougie, INDICES, type PlanIndice } from './plan';

const dax = INDICES[0];
const plan: PlanIndice = {
  source: 'Yahoo', regle: 'cassure-0.25-aucun', veille: '2026-10-27', cloture: 24000,
  ordres: [{ sens: 1, niveau: 24100, cote: 'haut', risque: 50 }, { sens: -1, niveau: 23900, cote: 'bas', risque: 50 }],
};
const t9 = Date.parse('2026-10-28T08:00:00Z');
const b = (k: number, o: number, h: number, l: number, c: number): Bougie => ({ t: t9 + k * 1_800_000, o, h, l, c });

describe('état du plan', () => {
  it('avant l’ouverture : attendre, séance pas encore ouverte', () => {
    const r = resumer(dax, Date.parse('2026-10-28T07:00:00Z'), [], [], plan);
    expect(r.etat.type).toBe('attendre');
    expect(r.info).toBe('séance pas encore ouverte');
    expect(r.ordres.map((o) => [o.stop, o.objectif])).toEqual([[24050, 24250], [23950, 23750]]);
  });

  it('niveau touché : en position, écart avec la veille en points', () => {
    const r = resumer(dax, t9 + 3_600_000, [b(0, 24050, 24120, 24040, 24110), b(1, 24110, 24130, 24090, 24120)], [], plan);
    expect(r.etat.type).toBe('position');
    expect(r.ecart).toBe(120);
    expect(r.ordres[0].distance).toBe(-20);
  });

  it('après l’heure limite sans entrée : rien aujourd’hui', () => {
    const r = resumer(dax, Date.parse('2026-10-28T15:30:00Z'), [b(0, 24000, 24050, 23950, 24010)], [], plan);
    expect(r.etat.type).toBe('rien');
  });
});
