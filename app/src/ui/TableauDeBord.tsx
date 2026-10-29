import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import Svg, { Circle, Line, Polyline, Rect, Text as SvgText } from 'react-native-svg';
import { type Tableau, dateFr, eur, nombre } from '../domain';
import { styles } from './Decisions';
import { type Couleurs, espace, useCouleurs } from './theme';

const HAUTEUR = 200;
const GAUCHE = 52; // place des montants
const HAUT = 16;
const BAS = 20;

function Tuile({ titre, valeur, sous, couleur, c }: { titre: string; valeur: string; sous: string; couleur: string; c: Couleurs }) {
  return (
    <View style={{ flexBasis: '47%', flexGrow: 1, borderWidth: 1, borderColor: c.ligne, borderRadius: 10, padding: espace(3) }}>
      <Text style={{ color: c.doux, fontSize: 12 }}>{titre}</Text>
      <Text style={{ color: couleur, fontSize: 24, fontWeight: '600', marginTop: espace(1) }}>{valeur}</Text>
      <Text style={{ color: c.doux, fontSize: 12 }}>{sous}</Text>
    </View>
  );
}

/** Barres : gain ou perte de chaque trade. Ligne : total cumulé. */
function Courbe({ t, c }: { t: Tableau; c: Couleurs }) {
  const [largeur, setLargeur] = useState(0);
  const [choisi, setChoisi] = useState<number | null>(null);
  const vals = [0, ...t.trades.map((x) => x.eur), ...t.cumul];
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const y = (v: number) => HAUT + ((hi - v) / (hi - lo || 1)) * (HAUTEUR - HAUT - BAS);
  const w = Math.max(largeur - GAUCHE, 1);
  const pas = w / Math.max(t.trades.length, 1);
  const x = (i: number) => GAUCHE + pas * (i + 0.5);
  const barre = Math.min(28, pas * 0.6);
  const sel = choisi !== null ? t.trades[choisi] : null;
  return (
    <View>
      <View onLayout={(e) => setLargeur(e.nativeEvent.layout.width)} style={{ height: HAUTEUR }}>
        {largeur > 0 && (
          <Svg width={largeur} height={HAUTEUR}>
            {[hi, 0, lo].filter((v, i, a) => a.indexOf(v) === i).map((v) => (
              <SvgText key={v} x={GAUCHE - 6} y={y(v) + 4} fontSize={11} fill={c.doux} textAnchor="end">{v === 0 ? '0 €' : eur(v)}</SvgText>
            ))}
            <Line x1={GAUCHE} x2={largeur} y1={y(0)} y2={y(0)} stroke={c.gris} strokeWidth={1} />
            {t.trades.map((tr, i) => (
              <Rect key={i} x={x(i) - barre / 2} width={barre} y={y(Math.max(0, tr.eur))} height={Math.max(1, Math.abs(y(tr.eur) - y(0)))}
                rx={3} fill={tr.eur > 0 ? c.vert : c.rouge} opacity={choisi === null || choisi === i ? 0.85 : 0.35} />
            ))}
            <Polyline points={t.cumul.map((v, i) => `${x(i)},${y(v)}`).join(' ')} fill="none" stroke={c.bleu} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
            {t.cumul.map((v, i) => <Circle key={i} cx={x(i)} cy={y(v)} r={i === t.cumul.length - 1 ? 4 : 2.5} fill={c.bleu} />)}
            {t.trades.map((tr, i) => (i === 0 || tr.date !== t.trades[i - 1].date) && (
              <SvgText key={`d${i}`} x={x(i)} y={HAUTEUR - 4} fontSize={10} fill={c.doux} textAnchor="middle">{tr.date.slice(8, 10)}/{tr.date.slice(5, 7)}</SvgText>
            ))}
          </Svg>
        )}
        <View style={{ position: 'absolute', left: GAUCHE, right: 0, top: 0, bottom: 0, flexDirection: 'row' }}>
          {t.trades.map((_, i) => <Pressable key={i} style={{ flex: 1 }} onPress={() => setChoisi(choisi === i ? null : i)} />)}
        </View>
      </View>
      <Text style={{ color: c.doux, fontSize: 13, marginTop: espace(1) }}>
        {sel && choisi !== null
          ? `${dateFr(sel.date)} · ${sel.type} · ${sel.nom} : ${eur(sel.eur)} (${sel.pts >= 0 ? '+' : '−'}${nombre(Math.abs(sel.pts), 0)} pts) · total ${eur(t.cumul[choisi])}`
          : 'Barres : chaque trade (vert gagné, rouge perdu). Ligne bleue : le total. Touche une barre pour le détail.'}
      </Text>
    </View>
  );
}

export function TableauDeBord({ t, risqueEur }: { t: Tableau; risqueEur: number }) {
  const c = useCouleurs();
  const doux = { color: c.doux, fontSize: 13 };
  const ligne = (titre: string, p: Tableau['parType']['intraday']) => (
    <Text style={[doux, { marginTop: espace(1) }]}>
      {titre} : {p.trades} terminé{p.trades > 1 ? 's' : ''}, {p.gagnes} gagné{p.gagnes > 1 ? 's' : ''} ·{' '}
      <Text style={{ color: p.totalEur >= 0 ? c.vert : c.rouge, fontWeight: '600' }}>{eur(p.totalEur)}</Text>
    </Text>
  );
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>📊 Gains et pertes des signaux</Text>
      {!t.trades.length && <Text style={doux}>Aucun trade terminé pour l’instant.</Text>}
      {t.trades.length > 0 && (
        <>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: espace(2) }}>
            <Tuile titre="Total" valeur={eur(t.totalEur)} sous={`${t.trades.length} trades terminés`} couleur={t.totalEur >= 0 ? c.vert : c.rouge} c={c} />
            <Tuile titre="Gains" valeur={eur(t.gainsEur)} sous={`${t.gagnes} gagné${t.gagnes > 1 ? 's' : ''}`} couleur={c.vert} c={c} />
            <Tuile titre="Pertes" valeur={eur(t.pertesEur)} sous={`${t.perdus} perdu${t.perdus > 1 ? 's' : ''} ou neutre${t.perdus > 1 ? 's' : ''}`} couleur={c.rouge} c={c} />
            <Tuile titre="En cours" valeur={String(t.enCours)} sous="positions swing ouvertes" couleur={c.texte} c={c} />
          </View>
          <View style={{ marginTop: espace(4) }}>
            <Courbe t={t} c={c} />
          </View>
          {ligne('⚡ Intraday', t.parType.intraday)}
          {ligne('📈 Swing', t.parType.swing)}
          <Text style={[doux, { marginTop: espace(2) }]}>
            Intraday : résultats réels du plan, en taille du plan. Swing : tous les signaux du scanner (actions comprises), comptés à {nombre(risqueEur, 0)} € de risque par trade (réglage plus bas).
          </Text>
        </>
      )}
    </View>
  );
}
