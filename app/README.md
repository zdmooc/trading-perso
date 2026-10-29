# Marché — application mobile

La page « marché » (DAX 40, Nasdaq 100, S&P 500) sur le téléphone : que faire maintenant, plan du jour,
cours, graphiques du jour et des 6 derniers mois. **Lecture seule : aucun ordre n'est jamais passé.**

Même pile que Déclic : React Native + Expo (TypeScript), APK Android via EAS Build, mises à jour sans
réinstaller via EAS Update depuis GitHub Actions.

## D'où viennent les chiffres

- **Cours** : Yahoo Finance, directement depuis le téléphone (gratuit, sans clé, sans serveur).
- **Plan du jour** : celui de 8h45 en cours IG s'il a été publié dans `reports/plan/`, sinon calculé sur
  le téléphone avec la même règle (cassure du plus haut / plus bas de la veille, objectif 3 fois le risque).
  Les niveaux Yahoo et IG peuvent différer de quelques points.
- **Règle de chaque indice et résultats du test** : `reports/plan/stats.json`.

Les calculs (`src/domain/plan.ts`) sont un portage de `src/tradeperso/plan.py`. Le test de parité compare
avec des cas produits par le code Python : `python app/scripts/parite.py` les régénère.

## Trois onglets

- **⚡ Intraday** : plan du jour par indice, avec la taille de position (IG en contrats, eToro en unités,
  spread compris) pour le risque en € choisi dans les réglages.
- **📈 Swing** : règles longues du scanner, filtre S&P 500 / moyenne 200 jours.
- **📒 Bilan** : mes trades (bouton « ✋ J'ai pris ce trade », puis clôture), mes résultats, résultats
  réels du plan et du scanner, réglages.

- **🟢 eToro** : mon compte eToro (positions, gain ou perte en cours) et les achats / ventes du plan et du
  scanner recalés sur le cours eToro, avec les unités pour le risque choisi. Clés API eToro « lecture »
  saisies dans l'onglet, gardées sur le téléphone ; `src/adapters/etoro.ts` ne fait que des GET.

Les trades notés restent sur le téléphone (`expo-sqlite`). Les alertes (entrée proche, entrée touchée,
stop, objectif) sont des notifications locales : à chaque rafraîchissement quand l'app est ouverte,
et au mieux toutes les 15 min en arrière-plan (Android décide du moment exact).

Depuis la version 0.2.0 (modules natifs ajoutés), un nouvel APK est nécessaire : Actions → app-publier
→ Run workflow avec « apk » coché.

## Installer sur Android (une seule fois, depuis le PC)

```bash
cd app
npm install
npx eas-cli@latest init                # crée le projet « marche-trading-perso » sur expo.dev
npx eas-cli@latest update:configure    # active les mises à jour sans réinstaller
npx eas-cli@latest build -p android --profile preview   # APK, lien de téléchargement à la fin
```

Ensuite, chaque modification de `app/` poussée sur `main` arrive sur le téléphone tout seul
(workflow `app-publier`, secret `EXPO_TOKEN` à ajouter une fois dans les secrets du dépôt).

## Développer

```bash
npm start          # puis scanner le QR code avec Expo Go
npm test
npm run typecheck
npm run lint
```
