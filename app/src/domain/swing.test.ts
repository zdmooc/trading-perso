import { describe, expect, it } from 'vitest';
import parite from './__fixtures__/parite_swing.json';
import type { Bougie } from './plan';
import { REGLES_SWING, analyserSwing } from './swing';

/** Cas calculés par strategies.py (app/scripts/parite_swing.py) : mêmes signaux, mêmes stops, mêmes objectifs. */
const cas = parite as unknown as { bougies: Bougie[]; regles: Record<string, { entree: boolean[]; stop: (number | null)[]; objectif: (number | null)[] }> }[];

describe.each(REGLES_SWING)('parité avec Python : $cle', (r) => {
  it.each(cas.map((c, i) => [i, c] as const))('série %i', (_, c) => {
    const k = r.calculer(c.bougies);
    const py = c.regles[r.cle];
    expect(k.entree).toEqual(py.entree);
    py.entree.forEach((e, i) => {
      if (!e) return;
      expect(k.stop[i]).toBeCloseTo(py.stop[i] as number, 6);
      expect(k.objectif[i]).toBeCloseTo(py.objectif[i] as number, 6);
    });
  });
});

describe('analyserSwing', () => {
  const b = cas[0].bougies;

  it('filtre de marché : pas d’achat en marché baissier, pas de vente en marché haussier', () => {
    for (let n = 250; n <= b.length; n += 5) {
      const s = analyserSwing(b.slice(0, n), '', false);
      expect(s?.signaux.every((x) => x.regle.sens < 0)).toBe(true);
      expect(analyserSwing(b.slice(0, n), '', true)?.signaux.every((x) => x.regle.sens > 0)).toBe(true);
    }
  });

  it('trouve le signal du jour quand une règle se déclenche à la dernière clôture', () => {
    const i = cas[0].regles.cassure_20j.entree.lastIndexOf(true);
    const s = analyserSwing(b.slice(0, i + 1), '', null);
    expect(s?.signaux.map((x) => x.regle.cle)).toContain('cassure_20j');
  });
});
