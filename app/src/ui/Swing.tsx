import { Pressable, Text, View } from 'react-native';
import { type Bougie, type Indice, type Swing, dateFr, eur, nombre, pts, sma, variation } from '../domain';
import type { LigneJournal } from '../adapters/depot';
import { Graphique, type Niveau } from './Graphique';
import { styles } from './Decisions';
import { LigneTaille } from './LigneTaille';
import { BoutonPris, type Proposition } from './PrendreTrade';
import { type Couleurs, espace, useCouleurs } from './theme';

const n = (x: number) => nombre(x, 0);
const EN_COURS = ['ouvert', 'en attente'];

function Badge({ texte, fond }: { texte: string; fond: string }) {
  return <Text style={[styles.badge, { backgroundColor: fond }]}>{texte}</Text>;
}

function Niveaux({ c, entree, stop, objectif }: { c: Couleurs; entree: string; stop: string; objectif: string }) {
  return (
    <View style={styles.niveaux}>
      <Text style={{ color: c.doux, fontSize: 13 }}>Entrée <Text style={{ color: c.texte }}>{entree}</Text></Text>
      <Text style={{ color: c.doux, fontSize: 13 }}>Stop <Text style={{ color: c.rouge }}>{stop}</Text></Text>
      <Text style={{ color: c.doux, fontSize: 13 }}>Objectif <Text style={{ color: c.vert }}>{objectif}</Text></Text>
    </View>
  );
}

/** Position du scanner encore en cours sur cet indice (journal publié par GitHub Actions). */
function enCours(journal: LigneJournal[], symbole: string): LigneJournal | undefined {
  return journal.filter((l) => l.symbole === symbole && EN_COURS.includes(l.statut)).pop();
}

function Etat({ ind, s, pos, c }: { ind: Indice; s: Swing | null; pos?: LigneJournal; c: Couleurs }) {
  if (pos && pos.statut === 'ouvert' && s) {
    const latent = pos.sens * (s.cours - pos.prix_entree);
    return (
      <>
        <Badge texte={`EN POSITION · ${pos.sens > 0 ? 'ACHAT' : 'VENTE'}`} fond={pos.sens > 0 ? c.vert : c.rouge} />
        <Text style={{ color: latent >= 0 ? c.vert : c.rouge, fontSize: 16, fontWeight: '600' }}>{pts(latent)} = {eur(latent * ind.taille)}</Text>
      </>
    );
  }
  if (pos || s?.signaux.length) {
    const sens = pos ? pos.sens : (s as Swing).signaux[0].regle.sens;
    return <><Badge texte={`SIGNAL · ${sens > 0 ? 'ACHAT' : 'VENTE'}`} fond={sens > 0 ? c.vert : c.rouge} />
      <Text style={{ color: c.texte }}>entrée à l’ouverture de la prochaine séance</Text></>;
  }
  return <><Badge texte="RIEN À FAIRE" fond={c.gris} />{s && <Text style={{ color: c.doux }}>tendance {s.tendance}</Text>}</>;
}

export function ResumeSwing({ indices, swing, journal, choisi, onChoisir }: {
  indices: Indice[]; swing: Record<string, Swing | null>; journal: LigneJournal[]; choisi: string; onChoisir: (s: string) => void;
}) {
  const c = useCouleurs();
  const marche = Object.values(swing).find((s) => s)?.marcheHaussier;
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>📈 Swing : positions de quelques jours</Text>
      {indices.map((ind, i) => {
        const s = swing[ind.symbole];
        return (
          <Pressable key={ind.symbole} onPress={() => onChoisir(ind.symbole)}
            style={[styles.ligne, i > 0 && { borderTopWidth: 1, borderTopColor: c.ligne }, ind.symbole === choisi && styles.choisi, ind.symbole === choisi && { borderLeftColor: c.bleu }]}>
            <Text style={[styles.nom, { color: c.texte }]}>
              {ind.drapeau} {ind.nom} <Text style={{ color: c.doux, fontWeight: '400' }}>{s ? n(s.cours) : '—'}</Text>
            </Text>
            <Etat ind={ind} s={s} pos={enCours(journal, ind.symbole)} c={c} />
          </Pressable>
        );
      })}
      <Text style={{ color: c.doux, fontSize: 12, marginTop: espace(2) }}>
        {marche === true ? 'Marché haussier (S&P 500 au-dessus de sa moyenne 200 jours) : achats seulement. '
          : marche === false ? 'Marché baissier (S&P 500 sous sa moyenne 200 jours) : ventes seulement. ' : ''}
        Calculé sur les clôtures. Touche un indice pour voir son détail.
      </Text>
    </View>
  );
}

export function CarteSwing({ ind, s, quotidien, journal, risqueEur, eurUsd, onPrendre }: {
  ind: Indice; s: Swing | null; quotidien: Bougie[]; journal: LigneJournal[]; risqueEur: number; eurUsd: number; onPrendre: (p: Proposition) => void;
}) {
  const c = useCouleurs();
  const doux = { color: c.doux, fontSize: 13 };
  if (!s) {
    return <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}><Text style={doux}>Pas assez de cours.</Text></View>;
  }
  const pos = enCours(journal, ind.symbole);
  const clos = journal.filter((l) => l.symbole === ind.symbole && !EN_COURS.includes(l.statut) && l.statut !== 'annulé').slice(-3).reverse();
  const niveaux: Niveau[] = [
    { y: s.plusHaut20, couleur: c.vert, texte: '+haut 20 j', tirets: true },
    { y: s.plusBas20, couleur: c.rouge, texte: '+bas 20 j', tirets: true },
  ];
  if (pos) {
    niveaux.push({ y: pos.stop, couleur: c.gris, texte: 'stop' }, { y: pos.objectif, couleur: c.bleu, texte: 'obj.' });
  }
  const an = quotidien.slice(-250);
  const cl = quotidien.map((b) => b.c);
  const achatsPermis = s.marcheHaussier !== false;
  const ventesPermises = s.marcheHaussier !== true;
  const lent = s.mm200 ?? s.mm50;
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>{ind.drapeau} {ind.nom} · swing</Text>
      <Text style={{ color: c.texte, fontSize: 28, fontWeight: '600' }}>{n(s.cours)} <Text style={doux}>clôture du {dateFr(s.date)}</Text></Text>
      <Text style={doux}>Tendance {s.tendance}{s.rsi !== null ? ` · RSI 14 jours ${Math.round(s.rsi)}${s.rsi >= 70 ? ' (surachat)' : s.rsi <= 30 ? ' (survente)' : ''}` : ''}</Text>

      {pos && (
        <View style={{ marginTop: espace(3), gap: espace(1) }}>
          <Text style={[styles.nom, { color: c.texte }]}>Position du scanner</Text>
          <Etat ind={ind} s={s} pos={pos} c={c} />
          <Text style={doux}>Signal du {dateFr(pos.date_signal)}{pos.statut === 'ouvert' ? `, entrée le ${dateFr(pos.date_entree)}` : ''}</Text>
          <Niveaux c={c} entree={n(pos.statut === 'ouvert' ? pos.prix_entree : pos.entree_prevue)}
            stop={`${n(pos.stop)} (${eur(-Math.abs(pos.entree_prevue - pos.stop) * ind.taille)})`}
            objectif={`${n(pos.objectif)} (${eur(Math.abs(pos.objectif - pos.entree_prevue) * ind.taille)})`} />
          <BoutonPris onPress={() => onPrendre({ symbole: ind.symbole, type: 'swing', sens: pos.sens > 0 ? 1 : -1,
            entree: pos.statut === 'ouvert' ? pos.prix_entree : pos.entree_prevue, stop: pos.stop, objectif: pos.objectif })} />
        </View>
      )}

      {s.signaux.map((x) => (
        <View key={x.regle.cle} style={{ marginTop: espace(3), gap: espace(1) }}>
          <Badge texte={`SIGNAL · ${x.regle.sens > 0 ? 'ACHAT' : 'VENTE'}`} fond={x.regle.sens > 0 ? c.vert : c.rouge} />
          <Text style={{ color: c.texte }}>{x.regle.nom} : entrée à l’ouverture de la prochaine séance, vers {n(x.cours)}</Text>
          <Niveaux c={c} entree={n(x.cours)} stop={`${n(x.stop)} (${eur(-Math.abs(x.cours - x.stop) * ind.taille)})`}
            objectif={`${n(x.objectif)} (${eur(Math.abs(x.objectif - x.cours) * ind.taille)})`} />
          <LigneTaille ind={ind} entree={x.cours} stop={x.stop} risqueEur={risqueEur} eurUsd={eurUsd} />
          <BoutonPris onPress={() => onPrendre({ symbole: ind.symbole, type: 'swing', sens: x.regle.sens, entree: x.cours, stop: x.stop, objectif: x.objectif })} />
        </View>
      ))}

      <Text style={[styles.nom, { color: c.texte, marginTop: espace(4) }]}>À surveiller</Text>
      {achatsPermis && lent !== null && s.cours > lent && (
        <Text style={{ color: c.texte }}>🟢 Achat si clôture au-dessus de <Text style={{ fontWeight: '700' }}>{n(s.plusHaut20)}</Text>
          <Text style={doux}> (plus haut 20 jours, {variation(s.plusHaut20 - s.cours, s.cours)})</Text></Text>
      )}
      {ventesPermises && lent !== null && s.cours < lent && (
        <Text style={{ color: c.texte }}>🔴 Vente si clôture sous <Text style={{ fontWeight: '700' }}>{n(s.plusBas20)}</Text>
          <Text style={doux}> (plus bas 20 jours, {variation(s.plusBas20 - s.cours, s.cours)})</Text></Text>
      )}
      {s.mm50 !== null && <Text style={doux}>Moyenne 50 jours {n(s.mm50)} : cours {variation(s.cours - s.mm50, s.mm50)}</Text>}
      {s.mm200 !== null && <Text style={doux}>Moyenne 200 jours {n(s.mm200)} : cours {variation(s.cours - s.mm200, s.mm200)}</Text>}

      <Text style={[doux, { marginTop: espace(4), marginBottom: espace(1) }]}>
        1 an · <Text style={{ color: c.bleu }}>moy. 20 j</Text> · <Text style={{ color: c.orange }}>moy. 50 j</Text> · <Text style={{ color: c.texte }}>moy. 200 j</Text>
      </Text>
      <Graphique bougies={an} hauteur={240} niveaux={niveaux} series={[
        { valeurs: sma(cl, 20).slice(-250), couleur: c.bleu },
        { valeurs: sma(cl, 50).slice(-250), couleur: c.orange },
        { valeurs: sma(cl, 200).slice(-250), couleur: c.texte },
      ]} />

      {clos.length > 0 && (
        <>
          <Text style={[styles.nom, { color: c.texte, marginTop: espace(4) }]}>Derniers trades swing</Text>
          {clos.map((l) => {
            const p = l.sens * (l.prix_sortie - l.prix_entree);
            return (
              <Text key={l.date_signal + l.strategie} style={doux}>
                {dateFr(l.date_entree)} → {dateFr(l.date_sortie)} · {l.sens > 0 ? 'achat' : 'vente'} {n(l.prix_entree)}, {l.motif} :{' '}
                <Text style={{ color: p >= 0 ? c.vert : c.rouge }}>{pts(p)} = {eur(p * ind.taille)}</Text>
              </Text>
            );
          })}
        </>
      )}
      <Text style={[doux, { marginTop: espace(3), fontSize: 12 }]}>Montants en € pour la taille du plan ({nombre(ind.taille, 1)} €/pt).</Text>
    </View>
  );
}
