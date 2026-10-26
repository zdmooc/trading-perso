# Première expérience eToro NSDQ100 — 26 octobre 2026

Statut : **EXPÉRIENCE EXPLORATOIRE, NON REPRODUCTIBLE À PARTIR DU SEUL DÉPÔT**. Les données brutes eToro ne sont pas republiées; ce rapport documente les chiffres de l'exécution immédiate, sans prétendre que le pipeline `experiment.py` a été exécuté sur elles.

## Source et échantillon

- Connecteur eToro, instrument `NSDQ100` (ID 28), chandeliers `1d`, côté **bid**, 2000 observations du 2019-02-14 au 2026-10-24.
- 1 978 observations dérivées après le chauffage des indicateurs et suppression du dernier label.
- Découpage dans l'ordre chronologique : 1 383 entraînement, 296 validation, 297 test, avec purge d'une séance.
- Variables au close J : rendement J, rendement 5 jours, écart MM20, range / open, gap / close précédent, volatilité 20 jours.
- Label : `(Close[J+1] / Open[J+1]) - 1 > 0`. Hypothèse d'achat à l'ouverture et vente à la clôture J+1; pas de ventes à découvert.
- Frais hypothétiques **15 points de base aller-retour**, seuil fixe de probabilité 0,55.
- Modèles exploratoires entraînés/calculés dans une exécution isolée **JavaScript** : classe majoritaire/probabilité a priori, régression logistique pénalisée, arbre à une séparation (*decision stump*). **Ils ne sont pas identiques** aux trois candidats sklearn du fichier `experiment.py`.

## Validation (hors entraînement)

| Modèle | Brier | Signaux | Rendement net théorique | Max drawdown théorique |
|---|---:|---:|---:|---:|
| Prior only | 0,24676 | 0 | 0 % | 0 % |
| Régression logistique | 0,24948 | 194 | -14,659 % | -28,159 % |
| Arbre une séparation | 0,24867 | 265 | -11,665 % | -29,230 % |

Le modèle « prior only » / abstention a été sélectionné sur validation selon le critère de rendement net.

## Test final hors échantillon

- **Champion** : prior only — **0 signal / 297 séances**, rendement simulé **0 %**, drawdown **0 %**, Brier **0,24862**.
- **Conclusion : AUCUNE PREUVE D'AVANTAGE PRÉDICTIF NI DE RENTABILITÉ**.
- Ce résultat n'est pas une démonstration de stratégie gagnante, seulement une première comparaison honnête face à l'abstention.

## Limitations majeures

1. Recherche exploratoire : un seul découpage temporel, pas de walk-forward répété, ni d'intervalle de confiance, ni d'expérience causale indépendante reproductible sur les mêmes bougies conservées.
2. Les chandeliers CFD eToro sont des chandeliers *bid*, pas un flux tick ask+bid : le spread et les frais réels du courtier **ne sont pas reconstitués**.
3. L'hypothèse 15 bps est fixe, pas le tarif eToro/IG; financement, gaps, latence, requotes et conversion restent à vérifier.
4. Sans fichier brut conservé ni hash, cette exécution ne constitue pas une preuve auditable au niveau production.
5. L'indice `^NDX` (Nasdaq 100 cash) et le CFD eToro `NSDQ100` ne sont pas interchangeables.

## Prochaine expérience

Implémenter l'import local privé de données de chandeliers eToro au format OHLC, conserver hash et provenance, exécuter `experiment.py` (scikit-learn) sur cet historique, répéter le walk-forward et appliquer un modèle de coûts propre à l'instrument eToro/IG. Ne pas passer d'ordre réel.
