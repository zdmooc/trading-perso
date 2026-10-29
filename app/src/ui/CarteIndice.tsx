import { Text, View } from 'react-native';
import { type Resume, dateFr, eur, fenetre, nombre, pts, variation } from '../domain';
import type { StatsRegle } from '../adapters/depot';
import { Graphique, type Niveau } from './Graphique';
import { styles } from './Decisions';
import { espace, useCouleurs } from './theme';

const n = (x: number) => nombre(x, 0);

export function CarteIndice({ r, stats, debutTest }: { r: Resume; stats?: StatsRegle; debutTest?: string }) {
  const c = useCouleurs();
  const niveaux: Niveau[] = [];
  for (const o of r.ordres) {
    niveaux.push({ y: o.niveau, couleur: o.sens > 0 ? c.vert : c.rouge, texte: o.sens > 0 ? 'Achat' : 'Vente' });
    niveaux.push({ y: o.stop, couleur: c.gris, texte: 'stop', tirets: true });
    niveaux.push({ y: o.objectif, couleur: c.bleu, texte: 'obj.', tirets: true });
  }
  for (const [k, y] of Object.entries(r.pivots)) niveaux.push({ y, couleur: c.orange, texte: k, tirets: true });
  const ctx = r.contexte;
  const doux = { color: c.doux, fontSize: 13 };
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>{r.indice.drapeau} {r.indice.nom}</Text>
      {r.prix !== undefined && (
        <Text style={{ color: c.texte, fontSize: 28, fontWeight: '600' }}>
          {n(r.prix)} <Text style={doux}>à {r.heure}</Text>
        </Text>
      )}
      {r.ecart !== undefined && r.plan && (
        <Text style={{ color: r.ecart >= 0 ? c.vert : c.rouge, fontSize: 15 }}>
          {variation(r.ecart, r.plan.cloture)} <Text style={doux}>depuis la clôture d’hier</Text>
        </Text>
      )}
      {r.haut !== undefined && r.bas !== undefined && (
        <Text style={doux}>Plus haut du jour {n(r.haut)} · plus bas {n(r.bas)} · écart {n(r.haut - r.bas)} pts</Text>
      )}
      {r.plan && (
        <Text style={[doux, { marginTop: espace(1) }]}>
          Plan {r.plan.source === 'IG' ? 'de 8h45 (cours IG)' : 'calculé sur le téléphone (cours Yahoo)'} · veille du {dateFr(r.plan.veille)} · {fenetre(r.indice, r.date)}
        </Text>
      )}
      {stats && (
        <Text style={doux}>
          📊 Test{debutTest ? ` depuis ${dateFr(debutTest).split(' ').slice(2).join(' ')} ${debutTest.slice(0, 4)}` : ''} : {stats.trades} trades · {stats.gagnes_pct} % gagnés ({pts(stats.gain_moy)} en moy.) · total {pts(stats.total_pts)} = {eur(stats.total_eur)}
        </Text>
      )}
      {ctx && <Text style={doux}>Mouvement moyen d’une journée {n(ctx.atr)} pts</Text>}
      <Text style={[doux, { marginTop: espace(4), marginBottom: espace(1) }]}>{r.jour.length ? 'Aujourd’hui (bougies de 30 min)' : 'Dernière séance (bougies de 30 min)'}</Text>
      {r.graphe.length ? <Graphique bougies={r.graphe} niveaux={niveaux} hauteur={260} /> : <Text style={doux}>Pas de cours.</Text>}
    </View>
  );
}
