import { describe, expect, it } from 'vitest';
import parite from './__fixtures__/parite.json';
import { atr, rsi, sma } from './indicateurs';
import { type Bougie, INDICES, type Ordre, pivotsSemaine, preparer, rejouer, seances } from './plan';

/** Cas calculés par le code Python (app/scripts/parite.py) : l'app doit trouver les mêmes chiffres. */
const cas = parite.indices as unknown as Record<string, {
  quotidien: Bougie[]; intraday: Bougie[]; regle: string;
  plan: { veille: string; cloture: number; ordres: Ordre[] } | null;
  sma20: number[]; atr: number[]; rsi: number[]; pivots: Record<string, number>;
  rejeux: { jour: string; ordres: Ordre[]; trade: Record<string, number | string> | null }[];
}>;

const fin = <T>(x: T[]) => x.slice(-5);

describe.each(INDICES)('parité avec Python : $nom', (ind) => {
  const c = cas[ind.symbole];

  it('indicateurs (moyenne 20 j, ATR, RSI)', () => {
    const cl = c.quotidien.map((b) => b.c);
    fin(sma(cl, 20)).forEach((v, i) => expect(v).toBeCloseTo(c.sma20[i], 6));
    fin(atr(c.quotidien)).forEach((v, i) => expect(v).toBeCloseTo(c.atr[i], 6));
    fin(rsi(cl)).forEach((v, i) => expect(v).toBeCloseTo(c.rsi[i], 6));
  });

  it('plan du jour : mêmes niveaux, même risque', () => {
    const p = preparer(ind, '2026-10-28', c.quotidien, c.intraday, c.regle);
    expect(p?.veille).toBe(c.plan?.veille);
    expect(p?.cloture).toBeCloseTo(c.plan?.cloture as number, 6);
    expect(p?.ordres.length).toBe(c.plan?.ordres.length);
    p?.ordres.forEach((o, i) => {
      const r = c.plan?.ordres[i] as Ordre;
      expect([o.sens, o.cote]).toEqual([r.sens, r.cote]);
      expect(o.niveau).toBeCloseTo(r.niveau, 6);
      expect(o.risque).toBeCloseTo(r.risque, 6);
    });
  });

  it('rejeu des séances : même entrée, même sortie, mêmes points', () => {
    const ses = seances(c.intraday, ind);
    expect([...ses.keys()].sort()).toEqual([...new Set(c.rejeux.map((r) => r.jour))].sort());
    for (const r of c.rejeux) {
      const t = rejouer(ses.get(r.jour) as Bougie[], r.ordres, ind.finEntree, ind.spread, true);
      if (r.trade === null) {
        expect(t).toBeNull();
        continue;
      }
      expect(t?.motif).toBe(r.trade.motif);
      expect(t?.heure).toBe(r.trade.heure);
      expect(t?.entree).toBeCloseTo(r.trade.entree as number, 6);
      expect(t?.pts).toBeCloseTo(r.trade.pts as number, 6);
    }
  });

  it('pivots de la semaine', () => {
    const p = pivotsSemaine(c.quotidien, '2026-10-28');
    for (const k of Object.keys(c.pivots)) expect(p[k]).toBeCloseTo(c.pivots[k], 6);
  });
});

describe('rejouer', () => {
  const t0 = Date.parse('2026-10-28T08:00:00Z'); // 9h à Paris
  const b = (k: number, o: number, h: number, l: number, c: number): Bougie => ({ t: t0 + k * 1_800_000, o, h, l, c });
  const achat: Ordre = { sens: 1, niveau: 100, cote: 'haut', risque: 10 };

  it('rien de touché : pas de trade', () => {
    expect(rejouer([b(0, 95, 99, 94, 98)], [achat], 15, 1)).toBeNull();
  });

  it('séance pas finie : trade en cours, gain latent moins le spread', () => {
    const t = rejouer([b(0, 95, 101, 94, 100), b(1, 100, 112, 99, 110)], [achat], 15, 1, false);
    expect(t).toMatchObject({ entree: 100, stop: 90, objectif: 130, motif: 'en cours', heure: '09h', pts: 9 });
  });

  it('objectif à 3 fois le risque', () => {
    const t = rejouer([b(0, 95, 101, 94, 100), b(1, 100, 131, 99, 125)], [achat], 15, 1);
    expect(t).toMatchObject({ motif: 'objectif', pts: 29 });
  });

  it('pas d’entrée après l’heure limite', () => {
    const tard = { ...b(0, 95, 101, 94, 100), t: Date.parse('2026-10-28T15:30:00Z') }; // 16h30 à Paris
    expect(rejouer([tard], [achat], 15, 1)).toBeNull();
  });
});
