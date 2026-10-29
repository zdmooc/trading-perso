import { useState } from 'react';
import { Pressable, Switch, Text, TextInput, View } from 'react-native';
import { type Bilan, INDICES, type TradePerso, bilan, bilanPerso, dateFr, tableau, eur, euros, nombre, paris, points, pts } from '../domain';
import type { LigneJournal, LignePlan } from '../adapters/depot';
import { styles } from './Decisions';
import { CloturerTrade } from './PrendreTrade';
import { type MesDonnees, lireNombre } from './mesTrades';
import { TableauDeBord } from './TableauDeBord';
import { type Couleurs, espace, useCouleurs } from './theme';

const n = (x: number) => nombre(x, 0);
const pluriel = (k: number, mot: string) => `${k} ${mot}${k > 1 ? 's' : ''}`;
const ind = (s: string) => INDICES.find((i) => i.symbole === s) ?? INDICES[0];

function LigneBilan({ titre, b, c }: { titre: string; b: Bilan; c: Couleurs }) {
  if (!b.trades) return <Text style={{ color: c.doux, fontSize: 13, marginTop: espace(1) }}>{titre} : aucun trade clôturé</Text>;
  return (
    <View style={{ marginTop: espace(2) }}>
      <Text style={{ color: c.texte, fontWeight: '600' }}>
        {titre} : <Text style={{ color: b.totalEur >= 0 ? c.vert : c.rouge }}>{pts(b.totalPts)} = {eur(b.totalEur)}</Text>
      </Text>
      <Text style={{ color: c.doux, fontSize: 13 }}>
        {pluriel(b.trades, 'trade')} · {b.gagnes} gagné{b.gagnes > 1 ? 's' : ''}{b.gainMoyEur !== null ? ` (${eur(b.gainMoyEur)} en moy.)` : ''} · {b.perdus} perdu{b.perdus > 1 ? 's' : ''}{b.perteMoyEur !== null ? ` (${eur(b.perteMoyEur)} en moy.)` : ''}
      </Text>
    </View>
  );
}

function Carte({ titre, children, c }: { titre: string; children: React.ReactNode; c: Couleurs }) {
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>{titre}</Text>
      {children}
    </View>
  );
}

export function BilanEcran({ donnees, cours, planJournal, journal, journalTout }: {
  donnees: MesDonnees; cours: Record<string, number | undefined>; planJournal: LignePlan[]; journal: LigneJournal[]; journalTout: LigneJournal[];
}) {
  const c = useCouleurs();
  const [aCloturer, setACloturer] = useState<TradePerso | null>(null);
  const [risque, setRisque] = useState(nombre(donnees.reglages.risqueEur, 0));
  const { trades, reglages } = donnees;
  const ouverts = trades.filter((t) => t.sortie === undefined);
  const clos = trades.filter((t) => t.sortie !== undefined).sort((a, b) => (b.quandSortie ?? 0) - (a.quandSortie ?? 0));
  const doux = { color: c.doux, fontSize: 13 };

  const planClos = planJournal.filter((l) => l.statut === 'gagné' || l.statut === 'perdu');
  const swingClos = journal.filter((l) => ['succès', 'échec', 'neutre'].includes(l.statut));

  return (
    <View>
      <TableauDeBord t={tableau(planJournal, journalTout, reglages.risqueEur)} risqueEur={reglages.risqueEur} />

      <Carte titre="📒 Mes trades en cours" c={c}>
        {!ouverts.length && <Text style={doux}>Aucun. Touche « ✋ J’ai pris ce trade » sous un ordre pour en ajouter un.</Text>}
        {ouverts.map((t) => {
          const i = ind(t.symbole), p = points(t, cours[t.symbole]), e = euros(t, cours[t.symbole]);
          return (
            <View key={t.id} style={[styles.ligne, { borderTopWidth: 1, borderTopColor: c.ligne }]}>
              <Text style={[styles.nom, { color: c.texte }]}>{i.drapeau} {i.nom} · {t.sens > 0 ? 'achat' : 'vente'} {n(t.entree)} · {t.type} · {t.courtier}</Text>
              {p !== null && e !== null && <Text style={{ color: p >= 0 ? c.vert : c.rouge, fontSize: 16, fontWeight: '600' }}>{pts(p)} = {eur(e)}</Text>}
              <Text style={doux}>Stop {n(t.stop)} · objectif {n(t.objectif)} · {nombre(t.quantite, 2)} {t.courtier === 'IG' ? 'contrat' : 'unité'} · depuis le {dateFr(paris(t.quand).date)}</Text>
              <View style={{ flexDirection: 'row', gap: espace(3), marginTop: espace(1) }}>
                <Pressable onPress={() => setACloturer(t)}><Text style={{ color: c.bleu, fontWeight: '700' }}>Clôturer</Text></Pressable>
                <Pressable onPress={() => donnees.supprimer(t.id)}><Text style={{ color: c.doux }}>Supprimer</Text></Pressable>
              </View>
            </View>
          );
        })}
      </Carte>

      <Carte titre="🧾 Mes résultats" c={c}>
        <LigneBilan titre="⚡ Intraday" b={bilanPerso(trades, 'intraday')} c={c} />
        <LigneBilan titre="📈 Swing" b={bilanPerso(trades, 'swing')} c={c} />
        {clos.slice(0, 10).map((t) => {
          const p = points(t) as number, e = euros(t) as number, i = ind(t.symbole);
          return (
            <Text key={t.id} style={[doux, { marginTop: espace(1) }]}>
              {dateFr(paris(t.quandSortie ?? t.quand).date)} · {i.nom} {t.sens > 0 ? 'achat' : 'vente'} {n(t.entree)} → {n(t.sortie as number)} :{' '}
              <Text style={{ color: p >= 0 ? c.vert : c.rouge }}>{pts(p)} = {eur(e)}</Text>
              <Text onPress={() => donnees.supprimer(t.id)} style={{ color: c.doux }}>  ✕</Text>
            </Text>
          );
        })}
      </Carte>

      <Carte titre={`📋 Plan intraday réel${planJournal.length ? ` depuis le ${dateFr(planJournal[0].date)}` : ''}`} c={c}>
        {INDICES.map((i) => {
          const l = planClos.filter((x) => x.indice === i.nom);
          return <LigneBilan key={i.symbole} titre={`${i.drapeau} ${i.nom}`} b={bilan(l.map((x) => ({ pts: x.pts, eur: x.euros })))} c={c} />;
        })}
        <Text style={[doux, { marginTop: espace(2) }]}>
          Ce que le plan aurait fait, trade par trade, en taille du plan. Jours sans entrée touchée : {planJournal.filter((l) => l.statut === 'non déclenché').length}.
        </Text>
        {planClos.slice(-8).reverse().map((l) => (
          <Text key={l.date + l.indice} style={doux}>
            {dateFr(l.date)} · {l.indice} {l.sens} {n(l.entree)} ({l.heure}), {l.motif} :{' '}
            <Text style={{ color: l.pts >= 0 ? c.vert : c.rouge }}>{pts(l.pts)} = {eur(l.euros)}</Text>
          </Text>
        ))}
      </Carte>

      <Carte titre="📈 Swing du scanner sur les indices" c={c}>
        {!swingClos.length && <Text style={doux}>Aucun trade swing terminé sur les 3 indices pour l’instant.</Text>}
        {swingClos.slice(-8).reverse().map((l) => {
          const p = l.sens * (l.prix_sortie - l.prix_entree), i = ind(l.symbole);
          return (
            <Text key={l.date_signal + l.symbole + l.strategie} style={doux}>
              {dateFr(l.date_entree)} → {dateFr(l.date_sortie)} · {i.nom} {l.sens > 0 ? 'achat' : 'vente'} {n(l.prix_entree)}, {l.motif} :{' '}
              <Text style={{ color: p >= 0 ? c.vert : c.rouge }}>{pts(p)} = {eur(p * i.taille)}</Text>
            </Text>
          );
        })}
      </Carte>

      <Carte titre="⚙️ Réglages" c={c}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <Text style={{ color: c.texte, flex: 1, marginRight: espace(2) }}>Risque par trade (calcul de la taille)</Text>
          <TextInput value={risque} keyboardType="decimal-pad" onChangeText={setRisque}
            onEndEditing={() => {
              const v = lireNombre(risque);
              if (v !== null && v > 0) donnees.setReglages({ ...reglages, risqueEur: v });
              else setRisque(nombre(reglages.risqueEur, 0));
            }}
            style={{ color: c.texte, borderColor: c.ligne, borderWidth: 1, borderRadius: 8, width: 80, flexGrow: 0, textAlign: 'right', paddingHorizontal: espace(2), paddingVertical: espace(1), fontSize: 16 }} />
          <Text style={{ color: c.texte }}> €</Text>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: espace(3) }}>
          <Text style={{ color: c.texte, flex: 1 }}>🔔 Alertes : entrée proche, entrée touchée, stop, objectif</Text>
          <Switch value={reglages.alertes} onValueChange={(v) => donnees.setReglages({ ...reglages, alertes: v })} />
        </View>
        <Text style={[doux, { marginTop: espace(2) }]}>
          App fermée, Android vérifie au mieux toutes les 15 minutes : une alerte peut arriver avec quelques minutes de retard.
          Tes trades restent sur le téléphone.
        </Text>
      </Carte>

      {aCloturer && (
        <CloturerTrade titre={`Clôturer ${ind(aCloturer.symbole).nom} (${aCloturer.sens > 0 ? 'achat' : 'vente'} ${n(aCloturer.entree)})`}
          cours={cours[aCloturer.symbole]} onFermer={() => setACloturer(null)}
          onValider={(s) => {
            donnees.cloturer(aCloturer.id, s);
            setACloturer(null);
          }} />
      )}
    </View>
  );
}
