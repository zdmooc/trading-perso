import { Pressable, StyleSheet, Text, View } from 'react-native';
import { espace, useCouleurs } from './theme';

/** Rangée de boutons dont un seul est choisi (onglets, choix de l'indice). */
export function Choix<T extends string>({ options, valeur, onChoisir, grand = false }: {
  options: { cle: T; texte: string }[]; valeur: T; onChoisir: (v: T) => void; grand?: boolean;
}) {
  const c = useCouleurs();
  return (
    <View style={[styles.rangee, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      {options.map((o) => {
        const actif = o.cle === valeur;
        return (
          <Pressable key={o.cle} onPress={() => onChoisir(o.cle)} accessibilityRole="tab" accessibilityState={{ selected: actif }}
            style={[styles.bouton, { paddingVertical: grand ? espace(3) : espace(2) }, actif && { backgroundColor: c.bleu }]}>
            <Text numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.75}
              style={{ color: actif ? '#FFFFFF' : c.texte, fontSize: grand ? 16 : 14, fontWeight: actif ? '700' : '500' }}>{o.texte}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  rangee: { flexDirection: 'row', borderWidth: 1, borderRadius: 10, padding: 3, marginBottom: espace(4) },
  bouton: { flex: 1, alignItems: 'center', borderRadius: 8, paddingHorizontal: 2 },
});
