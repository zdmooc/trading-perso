import { Pressable, StyleSheet, Text, View } from 'react-native';
import { type Resume, eur, nombre, pts } from '../domain';
import { type Couleurs, espace, useCouleurs } from './theme';

const n = (x: number) => nombre(x, 0);

function Badge({ texte, fond }: { texte: string; fond: string }) {
  return <Text style={[styles.badge, { backgroundColor: fond }]}>{texte}</Text>;
}

/** Une ligne par indice : ce qu'il faut faire maintenant, avec entrée, stop et objectif bien visibles. */
function Ligne({ r, c }: { r: Resume; c: Couleurs }) {
  const e = r.etat;
  const taille = r.indice.taille;
  const tete = (
    <Text style={[styles.nom, { color: c.texte }]}>
      {r.indice.drapeau} {r.indice.nom} <Text style={{ color: c.doux, fontWeight: '400' }}>{r.prix !== undefined ? n(r.prix) : '—'}</Text>
    </Text>
  );
  if (e.type === 'pas-de-plan') {
    return <View style={styles.ligne}>{tete}<Text style={{ color: c.doux }}>Pas de plan aujourd’hui</Text></View>;
  }
  if (e.type === 'rien') {
    return <View style={styles.ligne}>{tete}<Badge texte="RIEN AUJOURD’HUI" fond={c.gris} /><Text style={{ color: c.doux }}>{e.raison}</Text></View>;
  }
  if (e.type === 'position' || e.type === 'termine') {
    const t = e.trade;
    const sens = t.sens > 0 ? 'ACHAT' : 'VENTE';
    const fin = { stop: 'stoppé', objectif: 'objectif atteint ✅', 'clôture': 'fermé en fin de séance', 'en cours': '' }[t.motif];
    return (
      <View style={[styles.ligne, e.type === 'position' && { backgroundColor: c.actif, borderRadius: 8, padding: espace(2) }]}>
        {tete}
        <Badge texte={e.type === 'position' ? `EN POSITION · ${sens}` : 'TERMINÉ'} fond={e.type === 'position' ? (t.sens > 0 ? c.vert : c.rouge) : c.gris} />
        <Text style={{ color: t.pts >= 0 ? c.vert : c.rouge, fontSize: 16, fontWeight: '600' }}>
          {fin ? `${fin} : ` : ''}{pts(t.pts)} = {eur(t.pts * taille)}
        </Text>
        <Niveaux c={c} entree={`${n(t.entree)} à ${t.heure}`} stop={n(t.stop)} objectif={n(t.objectif)} />
      </View>
    );
  }
  return (
    <View style={styles.ligne}>
      {tete}
      {r.info && <Text style={{ color: c.doux }}>{r.info}</Text>}
      {r.ordres.map((o, i) => {
        const achat = o.sens > 0;
        return (
          <View key={i} style={{ marginTop: espace(1) }}>
            <Badge texte={`ATTENDRE · ${achat ? 'ACHAT' : 'VENTE'}`} fond={achat ? c.vert : c.rouge} />
            <Text style={{ color: c.texte }}>
              si le cours <Text style={{ fontWeight: '700' }}>{o.cote === 'haut' ? 'monte' : 'descend'}</Text> à {n(o.niveau)}
              {o.distance !== null && <Text style={{ color: c.doux }}> · encore {n(Math.abs(o.distance))} pts</Text>}
            </Text>
            <Niveaux c={c} entree={n(o.niveau)} stop={`${n(o.stop)} (${eur(-o.risque * taille)})`} objectif={`${n(o.objectif)} (${eur(3 * o.risque * taille)})`} />
          </View>
        );
      })}
    </View>
  );
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

export function Decisions({ resumes, choisi, onChoisir }: { resumes: Resume[]; choisi: string; onChoisir: (s: string) => void }) {
  const c = useCouleurs();
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>🎯 Que faire maintenant</Text>
      {resumes.map((r, i) => (
        <Pressable key={r.indice.symbole} onPress={() => onChoisir(r.indice.symbole)}
          style={[i > 0 && { borderTopWidth: 1, borderTopColor: c.ligne }, r.indice.symbole === choisi && styles.choisi, r.indice.symbole === choisi && { borderLeftColor: c.bleu }]}>
          <Ligne r={r} c={c} />
        </Pressable>
      ))}
      <Text style={{ color: c.doux, fontSize: 12, marginTop: espace(2) }}>
        Touche un indice pour voir son détail. Un seul trade par indice et par jour. Dès qu’une entrée est touchée, l’autre est annulée.
      </Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  carte: { borderWidth: 1, borderRadius: 12, padding: espace(4), marginBottom: espace(4) },
  titre: { fontSize: 18, fontWeight: '700', marginBottom: espace(2) },
  ligne: { paddingVertical: espace(3), gap: espace(1) },
  nom: { fontSize: 16, fontWeight: '700' },
  badge: { alignSelf: 'flex-start', color: '#FFFFFF', fontSize: 12, fontWeight: '800', paddingHorizontal: espace(2), paddingVertical: 2, borderRadius: 6, overflow: 'hidden' },
  choisi: { borderLeftWidth: 3, paddingLeft: espace(2) },
  niveaux: { flexDirection: 'row', flexWrap: 'wrap', columnGap: espace(4), marginTop: 2 },
});
