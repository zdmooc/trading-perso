# Laboratoire IA trading — Hang Seng TECH (HSTECH)

**Un seul marché** : Hang Seng TECH, 30 valeurs technologiques de Hong Kong, prix théorique de l'indice `HSTECH.HK`. Le fait qu'un indice soit très volatil ne prouve ni sa négociabilité directe, ni qu'une IA peut le prévoir. **Simulation uniquement.** Aucun ordre transmis.

## Les 5 rôles, sur le même produit

| Étape | Rôle joué | Preuve à produire |
|---|---|---|
| 1 | Architecte Solutions IA | Objectif, architecture, contrat de données, risques, ADR |
| 2 | Data Scientist | Données OHLC réelles et datées, features causalement valides, modèles et test hors échantillon |
| 3 | AI Engineer | API prédiction en lecture seule et intégration avec le moteur de risque TradeOps |
| 4 | MLOps Engineer | Données et modèle versionnés, CI, métriques, dérive, MLflow, promotion conditionnelle |
| 5 | Platform Engineer | Conteneur, déploiement OpenShift/CRC, sondes, observabilité, arrêt sécurisé |

L'implémentation actuellement déposée couvre **l'expérience ML et les tests de mécanique (étape 2)**. Les étapes API, MLflow et OpenShift sont des travaux **à réaliser**, pas des déploiements déclarés.

## Expérience exécutable — première étape

Depuis la racine de `trading-perso` :

```bash
python -m pip install -e '.[dev]'
python -m pip install scikit-learn
python - <<'PY'
import pandas as pd
import yfinance as yf

df = yf.download("HSTECH.HK", period="5y", interval="1d",
                 auto_adjust=False, progress=False)
if df.empty:
    raise RuntimeError("Historique indisponible : vérifier la source / ticker")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df[["Open", "High", "Low", "Close"]].to_csv(
    "research/hstech-ai/hstech_daily.csv", index_label="Date"
)
print(len(df), "bougies téléchargées")
PY
python -m pytest -q research/hstech-ai/test_experiment.py
python research/hstech-ai/experiment.py --csv research/hstech-ai/hstech_daily.csv --output research/hstech-ai/results.json
```

Le téléchargement Yahoo est une source de recherche non officielle ; contrôler dates, fuseau, devise HKD, continuité et licences avant tout usage. Ne pas publier le CSV sans validation des droits. Ne pas confondre performances de l'indice avec résultats exécutables sur ETF, CFD ou futures.

## Protocole figé avant les résultats

- **Décision** : à la clôture J, prédire si le rendement ouverture → clôture de J+1 sera positif.
- **Action simulée** : long ou cash, sans vente à découvert ; entrée à l'ouverture J+1, sortie à la clôture J+1.
- **Données** : OHLC quotidiennes, aucune donnée future dans les variables J.
- **Modèles** : fréquence a priori (baseline), régression logistique, gradient boosting histogramme.
- **Validation** : 70 % entraînement, 15 % validation, 15 % test final, dans l'ordre temporel ; embargo/purge de 1 séance entre blocs.
- **Choix** : sur la validation seulement ; le test final est consulté après le choix.
- **Seuil** : 0,55 fixe ; coût hypothétique 15 points de base par aller-retour. Ce coût **n'est pas** un spread réel validé.
- **Métriques** : ROC-AUC, Brier, rendement net simulé, drawdown et nombre de signaux. Comparer le tout à « toujours long » avec les mêmes frais.
- **Critère d'avancement** : couverture des données et modèle hors échantillon vérifiés. Un excellent résultat synthétique ne compte **jamais** comme preuve d'alpha de marché.

Le modèle choisi est simplement le meilleur **parmi ces candidats**, pour **cette validation** ; ce n'est pas le meilleur modèle de trading au monde. L'étude ne corrige pas encore les biais de sélection ni la dépendance aux régimes de marché : avant la phase paper, ajouter walk-forward répété, intervalle de confiance et données de l'instrument effectivement négociable.

## Frontières d'architecture

```text
OHLC HSTECH -> contrôle qualité -> features à J -> modèle ML
  -> score / abstention -> Risk Gate déterministe -> revue humaine
  -> moteur de paper trading -> audit / métriques / dérive
                       (aucun ordre réel)
```

- Le **modèle trading** appartient à `trading-perso/research/hstech-ai`.
- Le **runtime agentique, MLflow, API, risque et OpenShift** doit réutiliser [TradeOps-GenAI-Integration](https://github.com/zdmooc/TradeOps-GenAI-Integration), pas être dupliqué ici.
- Les décisions d'architecture transverses utilisent [maya-ai-agentic-architecture-reference](https://github.com/zdmooc/maya-ai-agentic-architecture-reference).

**Prochain apprentissage à faire ensemble** : valider la qualité et la longueur de l'historique HSTECH, calculer son rendement et sa volatilité, puis expliquer chaque feature avant d'entraîner les modèles.
