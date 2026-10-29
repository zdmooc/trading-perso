import { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { type Courtier, INDICES, type TradePerso, type TypeTrade, eur, nombre, taille } from '../domain';
import { Choix } from './Onglets';
import { lireNombre } from './mesTrades';
import { espace, useCouleurs } from './theme';

export interface Proposition {
  symbole: string;
  type: TypeTrade;
  sens: 1 | -1;
  entree: number;
  stop: number;
  objectif: number;
}

const f = (x: number, d = 0) => nombre(x, d).replace(/\s/g, ' ');

/** « J'ai pris ce trade » : prix et taille préremplis, modifiables. */
export function PrendreTrade({ proposition, risqueEur, eurUsd, onFermer, onValider }: {
  proposition: Proposition; risqueEur: number; eurUsd: number; onFermer: () => void; onValider: (t: TradePerso) => void;
}) {
  const c = useCouleurs();
  const ind = INDICES.find((i) => i.symbole === proposition.symbole) ?? INDICES[0];
  const [courtier, setCourtier] = useState<Courtier>('IG');
  const tl = taille(ind, risqueEur, Math.abs(proposition.entree - proposition.stop), proposition.entree, eurUsd);
  const [champs, setChamps] = useState({
    entree: f(proposition.entree), stop: f(proposition.stop), objectif: f(proposition.objectif), quantite: nombre(tl.ig, 2),
  });
  const choisirCourtier = (k: Courtier) => {
    setCourtier(k);
    setChamps({ ...champs, quantite: nombre(k === 'IG' ? tl.ig : tl.etoro, 2) });
  };
  const v = { entree: lireNombre(champs.entree), stop: lireNombre(champs.stop), objectif: lireNombre(champs.objectif), quantite: lireNombre(champs.quantite) };
  const ok = v.entree !== null && v.stop !== null && v.objectif !== null && v.quantite !== null && v.quantite > 0;
  const fx = ind.symbole === '^GDAXI' ? 1 : eurUsd;
  const eurParPoint = v.quantite === null ? 0 : courtier === 'IG' ? v.quantite : v.quantite / fx;
  const champ = (cle: keyof typeof champs, libelle: string) => (
    <View style={styles.champ}>
      <Text style={{ color: c.doux, fontSize: 13 }}>{libelle}</Text>
      <TextInput value={champs[cle]} onChangeText={(t) => setChamps({ ...champs, [cle]: t })} keyboardType="decimal-pad"
        style={[styles.saisie, { color: c.texte, borderColor: c.ligne, backgroundColor: c.fond }]} />
    </View>
  );
  return (
    <Modal transparent animationType="slide" onRequestClose={onFermer}>
      <View style={styles.voile}>
        <View style={[styles.feuille, { backgroundColor: c.carte }]}>
          <Text style={{ color: c.texte, fontSize: 18, fontWeight: '700', marginBottom: espace(3) }}>
            {ind.drapeau} J’ai pris ce trade : {proposition.sens > 0 ? 'achat' : 'vente'} {ind.nom}
          </Text>
          <Choix options={[{ cle: 'IG' as const, texte: 'IG' }, { cle: 'eToro' as const, texte: 'eToro' }]} valeur={courtier} onChoisir={choisirCourtier} />
          <View style={styles.rangee}>{champ('entree', 'Entrée')}{champ('quantite', courtier === 'IG' ? 'Contrats (€/pt)' : 'Unités')}</View>
          <View style={styles.rangee}>{champ('stop', 'Stop')}{champ('objectif', 'Objectif')}</View>
          {ok && (
            <Text style={{ color: c.doux, fontSize: 13, marginBottom: espace(3) }}>
              Risque {eur(-Math.abs((v.entree as number) - (v.stop as number)) * eurParPoint)} · gain visé {eur(Math.abs((v.objectif as number) - (v.entree as number)) * eurParPoint)}
              {courtier === 'IG' && risqueEur / Math.abs(proposition.entree - proposition.stop) < tl.igMinimum ? ` · taille minimum IG ${nombre(tl.igMinimum, 1)} contrat` : ''}
            </Text>
          )}
          <View style={styles.rangee}>
            <Pressable onPress={onFermer} style={[styles.bouton, { borderColor: c.ligne, borderWidth: 1 }]}>
              <Text style={{ color: c.texte }}>Annuler</Text>
            </Pressable>
            <Pressable disabled={!ok} onPress={() => onValider({
              id: `${Date.now()}-${Math.round(Math.random() * 1e6)}`, quand: Date.now(), symbole: ind.symbole, type: proposition.type, courtier,
              sens: proposition.sens, entree: v.entree as number, stop: v.stop as number, objectif: v.objectif as number,
              quantite: v.quantite as number, eurParPoint,
            })} style={[styles.bouton, { backgroundColor: ok ? c.bleu : c.gris }]}>
              <Text style={{ color: '#FFFFFF', fontWeight: '700' }}>Enregistrer</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

/** Clôture d'un de mes trades : prix de sortie prérempli avec le cours du moment. */
export function CloturerTrade({ titre, cours, onFermer, onValider }: { titre: string; cours?: number; onFermer: () => void; onValider: (sortie: number) => void }) {
  const c = useCouleurs();
  const [texte, setTexte] = useState(cours === undefined ? '' : f(cours));
  const v = lireNombre(texte);
  return (
    <Modal transparent animationType="slide" onRequestClose={onFermer}>
      <View style={styles.voile}>
        <View style={[styles.feuille, { backgroundColor: c.carte }]}>
          <Text style={{ color: c.texte, fontSize: 18, fontWeight: '700', marginBottom: espace(3) }}>{titre}</Text>
          <View style={styles.champ}>
            <Text style={{ color: c.doux, fontSize: 13 }}>Prix de sortie</Text>
            <TextInput value={texte} onChangeText={setTexte} keyboardType="decimal-pad" autoFocus
              style={[styles.saisie, { color: c.texte, borderColor: c.ligne, backgroundColor: c.fond }]} />
          </View>
          <View style={styles.rangee}>
            <Pressable onPress={onFermer} style={[styles.bouton, { borderColor: c.ligne, borderWidth: 1 }]}><Text style={{ color: c.texte }}>Annuler</Text></Pressable>
            <Pressable disabled={v === null} onPress={() => onValider(v as number)} style={[styles.bouton, { backgroundColor: v === null ? c.gris : c.bleu }]}>
              <Text style={{ color: '#FFFFFF', fontWeight: '700' }}>Clôturer</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

/** Bouton discret sous un ordre ou un signal. */
export function BoutonPris({ onPress }: { onPress: () => void }) {
  const c = useCouleurs();
  return (
    <Pressable onPress={onPress} style={[styles.pris, { borderColor: c.bleu }]} accessibilityRole="button">
      <Text style={{ color: c.bleu, fontSize: 13, fontWeight: '600' }}>✋ J’ai pris ce trade</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  voile: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.45)' },
  feuille: { borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: espace(5), paddingBottom: espace(8) },
  rangee: { flexDirection: 'row', gap: espace(3) },
  champ: { flex: 1, marginBottom: espace(3) },
  saisie: { borderWidth: 1, borderRadius: 8, paddingHorizontal: espace(3), paddingVertical: espace(2), fontSize: 17, marginTop: 2 },
  bouton: { flex: 1, alignItems: 'center', paddingVertical: espace(3), borderRadius: 10 },
  pris: { alignSelf: 'flex-start', borderWidth: 1, borderRadius: 8, paddingHorizontal: espace(3), paddingVertical: espace(1), marginTop: espace(2) },
});
