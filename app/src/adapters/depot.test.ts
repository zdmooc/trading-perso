import { describe, expect, it } from 'vitest';
import { lireJournal } from './depot';

describe('journal des signaux swing', () => {
  it('lit les nombres, met « achat » par défaut et retire les doublons', () => {
    const j = lireJournal(`date_signal,symbole,nom,type,strategie,entree_prevue,stop,objectif,ratio,sens,statut,date_entree,prix_entree,date_sortie,prix_sortie,motif,r
2026-10-02,^NDX,Nasdaq 100,swing,cassure_20j,30807.9297,30035.3943,33125.5358,3.0,,échec,2026-10-05,30828.1661,2026-10-14,30020.3766,stop,-1.02
2026-10-02,^NDX,Nasdaq 100,swing,cassure_20j,30807.9297,30035.3943,33125.5358,3.0,,échec,2026-10-05,30828.1661,2026-10-14,30020.3766,stop,-1.02
2026-10-20,^GSPC,S&P 500,swing,tendance_mm_vente,7700,7800,7400,3.0,-1.0,ouvert,2026-10-21,7690,,,,
`);
    expect(j).toHaveLength(2);
    expect(j[0]).toMatchObject({ symbole: '^NDX', sens: 1, statut: 'échec', r: -1.02, stop: 30035.3943 });
    expect(j[1]).toMatchObject({ sens: -1, statut: 'ouvert', prix_entree: 7690 });
    expect(j[1].prix_sortie).toBeNaN();
  });
});
