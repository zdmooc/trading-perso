import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, Text, TextInput, View } from 'react-native';
import { type Resume, type Swing, INDICES, INSTRUMENTS, eur, nombre, pointsPosition, pts, recosEtoro } from '../domain';
import { type ClesEtoro, type DonneesEtoro, chargerEtoro } from '../adapters/etoro';
import { ecrireClesEtoro, lireClesEtoro } from '../adapters/stockage';
import { styles } from './Decisions';
import { type Couleurs, espace, useCouleurs } from './theme';

const n = (x: number) => nombre(x, 0);
const prix = (x: number) => nombre(x, x >= 1000 ? 0 : 2);

function Carte({ titre, children, c }: { titre: string; children: React.ReactNode; c: Couleurs }) {
  return (
    <View style={[styles.carte, { backgroundColor: c.carte, borderColor: c.ligne }]}>
      <Text style={[styles.titre, { color: c.texte }]}>{titre}</Text>
      {children}
    </View>
  );
}

function SaisieCles({ c, onValider }: { c: Couleurs; onValider: (k: ClesEtoro) => void }) {
  const [api, setApi] = useState('');
  const [user, setUser] = useState('');
  const champ = { color: c.texte, borderColor: c.ligne, borderWidth: 1, borderRadius: 8, paddingHorizontal: espace(2), paddingVertical: espace(2), marginTop: espace(1), fontSize: 14 };
  const doux = { color: c.doux, fontSize: 13 };
  return (
    <Carte titre="🔑 Relier mon compte eToro (lecture seule)" c={c}>
      <Text style={doux}>
        Sur eToro : Paramètres → Trading → Clés API → Créer une clé. Choisis l’environnement « Réel » et la permission « Lecture » seulement.
        eToro te donne deux clés : colle-les ici.
      </Text>
      <Text style={[doux, { marginTop: espace(3) }]}>Clé publique (API key)</Text>
      <TextInput value={api} onChangeText={setApi} autoCapitalize="none" autoCorrect={false} style={champ} />
      <Text style={[doux, { marginTop: espace(3) }]}>Clé utilisateur (user key)</Text>
      <TextInput value={user} onChangeText={setUser} autoCapitalize="none" autoCorrect={false} secureTextEntry style={champ} />
      <Pressable disabled={!api.trim() || !user.trim()} onPress={() => onValider({ api: api.trim(), user: user.trim() })}
        style={{ backgroundColor: api.trim() && user.trim() ? c.bleu : c.ligne, borderRadius: 8, paddingVertical: espace(3), alignItems: 'center', marginTop: espace(4) }}>
        <Text style={{ color: '#FFFFFF', fontWeight: '700' }}>Relier</Text>
      </Pressable>
      <Text style={[doux, { marginTop: espace(3) }]}>
        Les clés restent sur ce téléphone. L’app ne fait que lire ton compte : elle ne peut ni acheter, ni vendre, ni clôturer.
      </Text>
    </Carte>
  );
}

export function EtoroEcran({ resumes, swing, risqueEur, eurUsd, actualisation }: {
  resumes: Resume[]; swing: Record<string, Swing | null>; risqueEur: number; eurUsd: number; actualisation: number;
}) {
  const c = useCouleurs();
  const [cles, setCles] = useState<ClesEtoro | null>(lireClesEtoro);
  const [d, setD] = useState<DonneesEtoro | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const doux = { color: c.doux, fontSize: 13 };

  const charger = useCallback(async (k: ClesEtoro) => {
    try {
      const r = await chargerEtoro(k);
      setD(r);
      setErreur(null);
    } catch (e) {
      setErreur((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (!cles) return undefined;
    let annule = false;
    chargerEtoro(cles).then(
      (r) => !annule && (setD(r), setErreur(null)),
      (e: Error) => !annule && setErreur(e.message),
    );
    return () => {
      annule = true;
    };
  }, [cles, actualisation]);

  if (!cles) {
    return <SaisieCles c={c} onValider={(k) => {
      ecrireClesEtoro(k);
      setCles(k);
    }} />;
  }

  const enEur = (usd: number) => usd / eurUsd;
  const recos = d ? recosEtoro(resumes, swing, d.indices, risqueEur, eurUsd) : [];
  const ind = (s: string) => INDICES.find((i) => i.symbole === s) ?? INDICES[0];

  return (
    <View>
      {!d && !erreur && <ActivityIndicator style={{ marginVertical: espace(6) }} />}
      {erreur && <Text style={{ color: c.rouge, marginBottom: espace(4) }}>eToro : {erreur}</Text>}

      {d && (
        <Carte titre="💼 Mon compte eToro" c={c}>
          <View style={{ flexDirection: 'row', gap: espace(4) }}>
            {d.compte.pnlUsd !== null && (
              <View>
                <Text style={doux}>Gain ou perte en cours</Text>
                <Text style={{ color: d.compte.pnlUsd >= 0 ? c.vert : c.rouge, fontSize: 22, fontWeight: '600' }}>{eur(enEur(d.compte.pnlUsd))}</Text>
              </View>
            )}
            {d.compte.creditUsd !== null && (
              <View>
                <Text style={doux}>Disponible</Text>
                <Text style={{ color: c.texte, fontSize: 22, fontWeight: '600' }}>{n(enEur(d.compte.creditUsd))} €</Text>
              </View>
            )}
          </View>
          {!d.compte.positions.length && <Text style={[doux, { marginTop: espace(2) }]}>Aucune position ouverte.</Text>}
          {d.compte.positions.map((p) => {
            const pt = pointsPosition(p);
            return (
              <View key={p.id} style={[styles.ligne, { borderTopWidth: 1, borderTopColor: c.ligne }]}>
                <Text style={[styles.nom, { color: c.texte }]}>
                  {d.noms[p.instrumentId] ?? `Instrument ${p.instrumentId}`} · {p.achat ? 'achat' : 'vente'} · {nombre(p.unites, 2)} unités{p.levier > 1 ? ` · levier ${p.levier}` : ''}
                </Text>
                {p.pnlUsd !== null && (
                  <Text style={{ color: p.pnlUsd >= 0 ? c.vert : c.rouge, fontSize: 16, fontWeight: '600' }}>
                    {pt !== null ? `${pts(pt)} = ` : ''}{eur(enEur(p.pnlUsd))}
                  </Text>
                )}
                <Text style={doux}>
                  Ouvert à {prix(p.ouverture)}{p.actuel !== null ? `, maintenant ${prix(p.actuel)}` : ''}
                  {p.stop ? ` · stop ${prix(p.stop)}` : ' · pas de stop'}{p.objectif ? ` · objectif ${prix(p.objectif)}` : ''}
                  {p.depuis ? ` · depuis le ${p.depuis.slice(8, 10)}/${p.depuis.slice(5, 7)}` : ''}
                </Text>
              </View>
            );
          })}
        </Carte>
      )}

      {d && (
        <Carte titre="🎯 Achats et ventes à faire sur eToro" c={c}>
          {!recos.length && <Text style={doux}>Aucune recommandation pour le moment : pas d’ordre du plan en attente et pas de signal swing.</Text>}
          {recos.map((r, k) => {
            const i = ind(r.symbole);
            return (
              <View key={k} style={[styles.ligne, k > 0 && { borderTopWidth: 1, borderTopColor: c.ligne }]}>
                <Text style={{ color: r.sens > 0 ? c.vert : c.rouge, fontWeight: '700', fontSize: 16 }}>
                  {r.sens > 0 ? 'ACHAT' : 'VENTE'} {INSTRUMENTS[r.symbole].etoro} ({i.nom}) · {r.type === 'intraday' ? '⚡ intraday' : '📈 swing'}
                </Text>
                <Text style={{ color: c.texte }}>
                  Entrée {n(r.entree)} · stop {n(r.stop)} · objectif {n(r.objectif)}
                </Text>
                <Text style={{ color: c.texte }}>
                  {nombre(r.unites, 2)} unités · risque {eur(-r.risqueEur)} · objectif {eur(r.gainEur)}
                </Text>
                <Text style={doux}>
                  {r.quand}{r.regle ? ` · ${r.regle}` : ''} · spread eToro {nombre(r.spread, 1)} pts
                  {Math.abs(r.decalage) >= 1 ? ` · niveaux décalés de ${pts(r.decalage)} (cours eToro)` : ''}
                </Text>
              </View>
            );
          })}
          <Text style={[doux, { marginTop: espace(2) }]}>
            Mêmes règles que les onglets Intraday et Swing, recalées sur le cours eToro, pour {nombre(risqueEur, 0)} € de risque. C’est toi qui passes l’ordre sur eToro.
          </Text>
        </Carte>
      )}

      {d && d.suggestions.length > 0 && (
        <Carte titre="👀 Sélection eToro pour toi" c={c}>
          <Text style={doux}>Instruments proposés par eToro selon ton profil. Ce ne sont pas des signaux d’achat ni de vente.</Text>
          {d.suggestions.map((s) => (
            <Text key={s.id} style={{ color: c.texte, marginTop: espace(1) }}>
              {s.nom}{s.cote ? <Text style={doux}> · {prix((s.cote.bid + s.cote.ask) / 2)}</Text> : null}
            </Text>
          ))}
        </Carte>
      )}

      <View style={{ flexDirection: 'row', gap: espace(4), marginBottom: espace(8) }}>
        <Pressable onPress={() => void charger(cles)}><Text style={{ color: c.bleu, fontWeight: '700' }}>Actualiser eToro</Text></Pressable>
        <Pressable onPress={() => {
          ecrireClesEtoro(null);
          setCles(null);
          setD(null);
        }}><Text style={{ color: c.doux }}>Retirer mes clés</Text></Pressable>
      </View>
    </View>
  );
}
