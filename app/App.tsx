import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, AppState, RefreshControl, ScrollView, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { SOURCES } from './src/adapters/sources';
import { activerAlertes, prevenir } from './src/adapters/alertesTelephone';
import { type Marche, charger } from './src/application/marche';
import { INDICES, dateFr, hhmm, paris, weekEnd } from './src/domain';
import { BandeauMiseAJour } from './src/ui/BandeauMiseAJour';
import { CarteIndice } from './src/ui/CarteIndice';
import { Decisions } from './src/ui/Decisions';
import { Choix } from './src/ui/Onglets';
import { CarteSwing, ResumeSwing } from './src/ui/Swing';
import { BilanEcran } from './src/ui/Bilan';
import { EtoroEcran } from './src/ui/Etoro';
import { PrendreTrade, type Proposition } from './src/ui/PrendreTrade';
import { useMesDonnees } from './src/ui/mesTrades';
import { espace, useCouleurs } from './src/ui/theme';

const ONGLETS = [{ cle: 'intraday' as const, texte: '⚡ Intraday' }, { cle: 'swing' as const, texte: '📈 Swing' }, { cle: 'bilan' as const, texte: '📒 Bilan' }, { cle: 'etoro' as const, texte: '🟢 eToro' }];
const PUCES = INDICES.map((i) => ({ cle: i.symbole, texte: i.nom.replace(' 40', '').replace(' 100', '') }));
const RAFRAICHIR_MS = 5 * 60_000;

/** Écran unique : marché DAX / Nasdaq 100 / S&P 500, plan du jour et graphiques. Lecture seule, aucun ordre. */
export default function App() {
  const c = useCouleurs();
  const [marche, setMarche] = useState<Marche | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [onglet, setOnglet] = useState<'intraday' | 'swing' | 'bilan' | 'etoro'>('intraday');
  const [proposition, setProposition] = useState<Proposition | null>(null);
  const donnees = useMesDonnees();
  const [choisi, setChoisi] = useState(INDICES[0].symbole);

  const rafraichir = useCallback(async () => {
    setEnCours(true);
    try {
      const m = await charger(SOURCES);
      setMarche(m);
      setErreur(null);
      void prevenir(m.resumes).catch(() => undefined);
    } catch (e) {
      setErreur((e as Error).message);
    } finally {
      setEnCours(false);
    }
  }, []);

  useEffect(() => {
    void activerAlertes().catch(() => undefined);
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
              <Choix options={ONGLETS} valeur={onglet} onChoisir={setOnglet} grand />
              {onglet === 'intraday' ? (
                <>
                  {!weekEnd(marche.maintenant) && <Decisions resumes={marche.resumes} choisi={choisi} onChoisir={setChoisi} />}
                  <Choix options={PUCES} valeur={choisi} onChoisir={setChoisi} />
                  {marche.resumes.filter((r) => r.indice.symbole === choisi).map((r) => (
                    <CarteIndice key={r.indice.symbole} r={r} stats={marche.stats[r.indice.symbole]} debutTest={marche.debutTest}
                      risqueEur={donnees.reglages.risqueEur} eurUsd={marche.eurUsd} onPrendre={setProposition} />
                  ))}
                  <Text style={{ color: c.doux, fontSize: 12, marginBottom: espace(8) }}>
                    Lignes pleines : entrées du plan. Pointillés gris : stops. Pointillés bleus : objectifs (3 fois le risque).
                    Orange : pivots de la semaine. Les niveaux IG et les cours Yahoo peuvent différer de quelques points.
                    Montants en € pour la taille du plan (DAX et Nasdaq 0,5 contrat, S&P 500 1 contrat).
                  </Text>
                </>
              ) : onglet === 'etoro' ? (
                <EtoroEcran planJournal={marche.planJournal} resumes={marche.resumes} swing={marche.swing} risqueEur={donnees.reglages.risqueEur} eurUsd={marche.eurUsd}
                  actualisation={marche.maintenant} />
              ) : onglet === 'bilan' ? (
                <BilanEcran donnees={donnees} planJournal={marche.planJournal} journal={marche.journal} journalTout={marche.journalTout}
                  cours={Object.fromEntries(marche.resumes.map((r) => [r.indice.symbole, r.prix]))} />
              ) : (
                <>
                  <ResumeSwing indices={INDICES} swing={marche.swing} journal={marche.journal} choisi={choisi} onChoisir={setChoisi} />
                  <Choix options={PUCES} valeur={choisi} onChoisir={setChoisi} />
                  {INDICES.filter((i) => i.symbole === choisi).map((i) => (
                    <CarteSwing key={i.symbole} ind={i} s={marche.swing[i.symbole]} quotidien={marche.quotidien[i.symbole] ?? []} journal={marche.journal}
                      risqueEur={donnees.reglages.risqueEur} eurUsd={marche.eurUsd} onPrendre={setProposition} />
                  ))}
                  <View style={{ height: espace(8) }} />
                </>
              )}
            </View>
          )}
        </ScrollView>
        {proposition && marche && (
          <PrendreTrade proposition={proposition} risqueEur={donnees.reglages.risqueEur} eurUsd={marche.eurUsd}
            onFermer={() => setProposition(null)} onValider={(t) => {
              donnees.ajouter(t);
              setProposition(null);
              setOnglet('bilan');
            }} />
        )}
        <BandeauMiseAJour />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}
