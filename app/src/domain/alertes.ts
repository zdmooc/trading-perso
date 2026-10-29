/**
 * Alertes du plan intraday : cours proche d'une entrée, entrée touchée, stop ou objectif atteint.
 * Calcul pur : on compare l'état du moment au dernier état notifié, pour ne prévenir qu'une fois par événement.
 */
import { nombre, pts } from './format';
import type { Resume } from './marche';

/** Distance (points) sous laquelle on prévient qu'une entrée approche. */
export const PROCHE: Record<string, number> = { '^GDAXI': 20, '^NDX': 30, '^GSPC': 8 };

export interface Alerte {
  cle: string;
  titre: string;
  texte: string;
}

export function alertes(resumes: Resume[], dejaVues: Set<string>): Alerte[] {
  const out: Alerte[] = [];
  for (const r of resumes) {
    const n = r.indice.nom, jour = r.date, e = r.etat;
    const ajoute = (cle: string, titre: string, texte: string) => {
      const k = `${jour}|${r.indice.symbole}|${cle}`;
      if (!dejaVues.has(k)) out.push({ cle: k, titre, texte });
    };
    if (e.type === 'attendre' && r.prix !== undefined) {
      for (const o of r.ordres) {
        if (o.distance !== null && Math.abs(o.distance) <= (PROCHE[r.indice.symbole] ?? 20)) {
          ajoute(`proche${o.sens}`, `${r.indice.drapeau} ${n} : entrée proche`,
            `${o.sens > 0 ? 'Achat' : 'Vente'} à ${nombre(o.niveau, 0)}, cours ${nombre(r.prix, 0)} (encore ${nombre(Math.abs(o.distance), 0)} pts)`);
        }
      }
    }
    if (e.type === 'position' || e.type === 'termine') {
      const t = e.trade;
      ajoute('entree', `${r.indice.drapeau} ${n} : entrée touchée`,
        `${t.sens > 0 ? 'Achat' : 'Vente'} à ${nombre(t.entree, 0)} (${t.heure}) · stop ${nombre(t.stop, 0)} · objectif ${nombre(t.objectif, 0)}`);
    }
    if (e.type === 'termine' && (e.trade.motif === 'stop' || e.trade.motif === 'objectif')) {
      const t = e.trade;
      ajoute(t.motif, `${r.indice.drapeau} ${n} : ${t.motif === 'stop' ? 'stop touché' : 'objectif atteint ✅'}`,
        `${pts(t.pts)} = ${(t.pts * r.indice.taille >= 0 ? '+' : '−') + nombre(Math.abs(t.pts * r.indice.taille), 0)} €`);
    }
  }
  return out;
}
