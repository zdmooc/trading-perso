import { Pressable, StyleSheet, Text } from 'react-native';
import * as Updates from 'expo-updates';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { espace } from './theme';

/**
 * Mises à jour automatiques (EAS Update) : la nouvelle version est téléchargée en arrière-plan
 * au lancement ; ce bandeau propose de redémarrer pour l'appliquer tout de suite.
 */
export function BandeauMiseAJour() {
  const { isUpdatePending } = Updates.useUpdates();
  const insets = useSafeAreaInsets();
  if (!Updates.isEnabled || !isUpdatePending) return null;
  return (
    <Pressable style={[styles.bandeau, { paddingTop: insets.top + espace(2) }]} onPress={() => void Updates.reloadAsync()} accessibilityRole="button">
      <Text style={styles.texte}>Nouvelle version prête · </Text>
      <Text style={styles.action}>Redémarrer</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bandeau: {
    position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, elevation: 10, flexDirection: 'row', flexWrap: 'wrap',
    justifyContent: 'center', backgroundColor: '#22A06B', paddingVertical: espace(2), paddingHorizontal: espace(4),
  },
  texte: { color: '#FFFFFF', fontSize: 14 },
  action: { color: '#FFFFFF', fontSize: 14, fontWeight: '800', textDecorationLine: 'underline' },
});
