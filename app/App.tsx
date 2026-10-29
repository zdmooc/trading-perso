import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, AppState, RefreshControl, ScrollView, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { bougiesYahoo } from './src/adapters/yahoo';
import { planDepot, statsDepot } from './src/adapters/depot';
import { type Marche, charger } from './src/application/marche';
import { dateFr, hhmm, paris, weekEnd } from './src/domain';
import { BandeauMiseAJour } from './src/ui/BandeauMiseAJour';
import { CarteIndice } from './src/ui/CarteIndice';
import { Decisions } from './src/ui/Decisions';
import { espace, useCouleurs } from './src/ui/theme';

const SOURCES = { bougies: bougiesYahoo, stats: statsDepot, plan: planDepot };
const RAFRAICHIR_MS = 5 * 60_000;

/** Écran unique : marché DAX / Nasdaq 100 / S&P 500, plan du jour et graphiques. Lecture seule, aucun ordre. */
export default function App() {
  const c = useCouleurs();
  const [marche, setMarche] = useState<Marche | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const rafraichir = useCallback(async () => {
    setEnCours(true);
    try {
      setMarche(await charger(SOURCES));
      setErreur(null);
    } catch (e) {
      setErreur((e as Error).message);
    } finally {
      setEnCours(false);
    }
  }, []);

  useEffect(() => {
    void rafraichir();
    const minuterie = setInterval(() => {
      if (AppState.currentState === 'active') void rafraichir();
    }, RAFRAICHIR_MS);
    // Retour sur l'app : cours à jour tout de suite.
    const abo = AppState.addEventListener('change', (s) => s === 'active' && void rafraichir());
    return () => {
      clearInterval(minuterie);
      abo.remove();
    };
  }, [rafraichir]);

  const p = marche ? paris(marche.maintenant) : null;
  return (
    <SafeAreaProvider>
      <SafeAreaView style={{ flex: 1, backgroundColor: c.fond }} edges={['top', 'left', 'right']}>
        <StatusBar style="auto" />
        <ScrollView contentContainerStyle={{ padding: espace(4) }}
          refreshControl={<RefreshControl refreshing={enCours} onRefresh={() => void rafraichir()} />}>
          <Text style={{ color: c.texte, fontSize: 22, fontWeight: '700' }}>Marché{p ? ` à ${hhmm(p)}` : ''}</Text>
          <Text style={{ color: c.doux, fontSize: 13, marginBottom: espace(4) }}>
            {p ? `${dateFr(p.date)} · ` : ''}lecture seule, aucun ordre passé · tire vers le bas pour actualiser
          </Text>
          {marche && weekEnd(marche.maintenant) && (
            <Text style={{ color: c.texte, marginBottom: espace(4) }}>Week-end : marchés fermés, prochain plan lundi à 9h.</Text>
          )}
          {!marche && !erreur && <ActivityIndicator style={{ marginTop: espace(10) }} />}
          {erreur && <Text style={{ color: c.rouge, marginBottom: espace(4) }}>Cours indisponibles : {erreur}</Text>}
          {marche && marche.erreurs.length > 0 && (
            <Text style={{ color: c.orange, marginBottom: espace(4) }}>Certains cours manquent : {marche.erreurs[0]}</Text>
          )}
          {marche && (
            <View>
              {!weekEnd(marche.maintenant) && <Decisions resumes={marche.resumes} />}
              {marche.resumes.map((r) => (
                <CarteIndice key={r.indice.symbole} r={r} quotidien={marche.quotidien[r.indice.symbole] ?? []}
                  stats={marche.stats[r.indice.symbole]} debutTest={marche.debutTest} />
              ))}
              <Text style={{ color: c.doux, fontSize: 12, marginBottom: espace(8) }}>
                Lignes pleines : entrées du plan. Pointillés gris : stops. Pointillés bleus : objectifs (3 fois le risque).
                Orange : pivots de la semaine. Les niveaux IG et les cours Yahoo peuvent différer de quelques points.
                Montants en € pour la taille du plan (DAX et Nasdaq 0,5 contrat, S&P 500 1 contrat).
              </Text>
            </View>
          )}
        </ScrollView>
        <BandeauMiseAJour />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}
