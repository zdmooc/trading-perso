import { Text } from 'react-native';
import { type Indice, eur, nombre, taille } from '../domain';
import { useCouleurs } from './theme';

/** « Pour 30 € de risque : IG 0,5 contrat · eToro 1,6 unité », avec le spread. */
export function LigneTaille({ ind, entree, stop, risqueEur, eurUsd }: { ind: Indice; entree: number; stop: number; risqueEur: number; eurUsd: number }) {
  const c = useCouleurs();
  const ecart = Math.abs(entree - stop);
  if (!ecart) return null;
  const t = taille(ind, risqueEur, ecart, entree, eurUsd);
  return (
    <Text style={{ color: c.doux, fontSize: 12, marginTop: 2 }}>
      🧮 Pour {nombre(risqueEur, 0)} € de risque : IG {nombre(t.ig, 2)} contrat{t.ig > t.igMinimum ? '' : ' (minimum)'} = {eur(-t.igRisque)}, spread {nombre(t.igSpread, 1)} €
      {' · '}eToro {nombre(t.etoro, 2)} unité = {eur(-t.etoroRisque)}, spread {nombre(t.etoroSpread, 1)} €
    </Text>
  );
}
