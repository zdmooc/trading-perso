# Trading perso : scanner de signaux swing

Scanner personnel qui cherche chaque soir des opportunités swing sur **6 grands indices** (S&P 500, Nasdaq 100, DAX 40, Nikkei 225, FTSE 100, CAC 40), à l'achat comme à la vente, et sur **51 grandes actions US** (achat seulement, dont SpaceX depuis son entrée en bourse), avec entrée, stop, objectif et taille de position. Phase 1 (MVP) : **simulation uniquement, aucun ordre n'est passé**.

> **Avertissement.** Un signal n'est qu'une probabilité, jamais une garantie de gain. Les résultats passés ne préjugent pas des résultats futurs. Outil personnel, pas un conseil en investissement.

## Ce que fait le MVP

| Commande | Rôle |
| --- | --- |
| `tradeperso scan` | Signaux du jour → `reports/signaux.md`, suivi de tous les signaux → `reports/suivi.md` et `reports/journal.csv` (+ alerte Telegram si configurée) |
| `tradeperso backtest --period 10y` | Statistiques de chaque stratégie → `reports/backtest.md` |

Stratégies (bougies journalières ; achats filtrés par cours > MM200, ventes par cours < MM200) :

| Stratégie | Entrée | Stop | Sortie |
| --- | --- | --- | --- |
| `tendance_mm` | MM20 croise au-dessus de MM50 | 2 × ATR | objectif 3R (ratio 3,0), ou MM20 repasse sous MM50 |
| `rsi2_repli` | RSI(2) < 10 | 2,5 × ATR | objectif 1,5 ATR (ratio 0,6), ou clôture > MM5 |
| `cassure_20j` | clôture > plus haut 20 jours | 2 × ATR | objectif 3R (ratio 3,0), ou clôture < plus bas 10 jours |
| `repli_tendance` | tendance haussière (cours > MM50 > MM200), retour sur la MM20, puis clôture au-dessus du plus haut de la veille | sous le creux du repli | objectif 3R, ou clôture sous la MM50 |
| `tendance_mm_vente` (indices) | MM20 croise sous MM50 | 2 × ATR au-dessus | objectif 3R, ou MM20 repasse au-dessus de MM50 |
| `cassure_20j_vente` (indices) | clôture < plus bas 20 jours | 2 × ATR au-dessus | objectif 3R, ou clôture > plus haut 10 jours |

Seuls les signaux avec un **ratio gain/perte d'au moins 3 pour 1** (`ratio_min` dans `config.toml`) sont envoyés et suivis ; `rsi2_repli` (ratio 0,6) n'en produit donc plus.

Chaque signal indique son **sens** (achat ou vente), son **type** (`swing` pour l'instant ; le day trading arrive en phase 3) et son **ratio gain/perte** = |objectif − entrée| / |entrée − stop|.

**Nouvelles introductions en bourse** (ex. SpaceX) : tant qu'une action a moins de 200 séances, la tendance est jugée sur la moyenne 50 jours au lieu de la moyenne 200 jours. Les signaux peuvent donc partir dès 50 séances. Cette règle n'a pas pu être testée sur 10 ans (trop peu d'introductions dans la liste) : prudence.

## Spéculation (section `[speculation]` de `config.toml`)

Répartition proposée d'un capital de 10 000 € : **6 000 € sur un ETF gardé** (cœur), **3 000 € pour les signaux swing**, **1 000 € pour la spéculation**.

- **eToro, actions réelles sans levier** : chaque vendredi, les actions de la liste sont classées par leur hausse sur 6 mois comparée au S&P 500. Les 5 premières au-dessus de leur moyenne 50 jours sont détenues à parts égales. Une action est vendue si elle sort du top 10 ou repasse sous sa moyenne 50 jours ; tout est vendu si le S&P 500 passe sous sa moyenne 200 jours. Liste dans `reports/speculation.md`, message Telegram à chaque changement.
- **IG, options barrières** : pour chaque signal swing, le message donne le niveau de knock-out à placer (= le stop). La perte maximale est la prime payée, sans risque d'écart au-delà du stop. Disponible sur les indices et environ 90 actions chez IG.

## Protection du capital (section `[filtres]` de `config.toml`)

- **Filtre de marché** : achats seulement quand le S&P 500 est au-dessus de sa moyenne 200 jours ; ventes à découvert (indices) seulement quand il est en dessous.
- **Stop au prix d'entrée** : dès que le gain atteint 1 fois le risque (+1 R), le stop remonte au prix d'entrée. Le message donne le niveau à surveiller. Une sortie à ce niveau est comptée **neutre**.
- **Résultats d'entreprise** : pas d'achat d'une action dans les 5 jours de bourse avant sa publication de résultats (date Yahoo ; si elle est inconnue, le signal est gardé).
- **4 positions au maximum**, ouvertes ou en attente, et une seule par actif. Si plusieurs signaux tombent le même soir, les meilleurs ratios passent en premier.

## Suivi de chaque signal

Chaque signal est inscrit dans `reports/journal.csv` puis suivi chaque soir : entrée à l'ouverture suivante, puis sortie au stop (**échec**), à l'objectif ou sur signal de sortie (**succès** si le résultat est positif). Un signal dont l'ouverture tombe sous le stop est **annulé**. `reports/suivi.md` donne le nombre de succès et d'échecs, le taux de réussite et le résultat cumulé en R, au total et par stratégie ; le message Telegram rappelle le bilan.

## Comment passer un signal

Chaque signal indique :
- **Quand entrer** : à l'ouverture de la séance de Bourse qui suit la clôture du signal (New York 15:30, Francfort, Paris et Londres 9:00, Tokyo 1:00 ou 2:00, heure de Paris), au prix du marché. C'est l'ouverture de la Bourse, pas la bougie suivante sur IG ou eToro, qui cotent les indices presque 24 h/24. Les jours fériés ne sont pas encore gérés.
- **Où et quoi** : sur IG, un CFD (indice ou action) ; sur eToro, un CFD pour les indices et une **action réelle sans levier** pour les actions US (pas de frais de nuit).
- **Combien** : la quantité à ACHETER ou à VENDRE pour perdre environ 1 % du capital si le stop est touché. La vente à découvert se fait par CFD, sur les indices uniquement.
- **Ce que ça coûte** : spread + commissions aller-retour et financement par nuit pour les CFD, en euros. Les spreads viennent des pages officielles d'IG et d'eToro (heures principales) ; les taux de financement sont des estimations réglables dans `config.toml`.

Taille de position : `capital × risque_par_trade / (entrée − stop)`, réglable dans [`config.toml`](config.toml) avec la liste des actifs.

**Cœur + satellite** : le capital des signaux est fixé à 3 000 € (30 % du total) ; le reste est prévu sur un ETF Nasdaq 100 ou S&P 500 (UCITS) gardé sur la durée, qui a fait mieux que le système sur 2017-2026 (voir `reports/backtest.md`). Avec ce capital, 1 % de risque = 30 € par trade : quand les frais d'une plateforme dépassent 25 % de ce risque (souvent la commission minimum IG sur actions), le signal l'indique « à éviter ».

## Automatique, sans rien lancer

Le workflow GitHub Actions [`scan.yml`](.github/workflows/scan.yml) tourne gratuitement chaque soir de semaine à 22:30 UTC et le dimanche matin (backtest). Il publie les rapports dans `reports/`.

Pour recevoir les signaux sur Telegram (facultatif) :
1. Créez un bot avec @BotFather et récupérez son jeton.
2. Envoyez un message au bot, puis récupérez votre `chat_id` via `https://api.telegram.org/bot<JETON>/getUpdates`.
3. Dans GitHub : Settings → Secrets and variables → Actions → ajoutez `TELEGRAM_TOKEN` et `TELEGRAM_CHAT_ID`.

## En local

```bash
pip install -e '.[dev]'
pytest -q
tradeperso backtest
tradeperso scan
```

## Suite prévue

- Phase 2 : paper trading sur le compte **démo IG** (connecteur repris de TradeOps-GenAI-Integration), interface web, journal.
- Phase 3 : day trading (bougies 1 à 5 min).
- Phase 4 : argent réel en petite taille, ordres validés manuellement.

Limites connues : le rendement du backtest enchaîne les trades de tous les actifs par date de sortie (approximation, positions simultanées non plafonnées) ; données Yahoo gratuites, non officielles.

## Plan Europe (7h, 10h05, 17h45)

Workflow `plan-europe`, chaque jour de semaine, heure de Paris :

- **7h** : ce qu'ont fait les futures US, l'Asie, le pétrole, l'or et l'euro pendant la nuit ; pour le DAX, le CAC, l'Euro Stoxx et le FTSE : variation de la veille, amplitude attendue (ATR), repères (haut, bas, pivot) ; heures qui bougent le plus (2 ans de données horaires) ; déroulé de la journée. Rapport `reports/matin.md`.
- **10h05** : niveaux de la 1re heure (9h-10h). Achat au-dessus du plus haut, vente sous le plus bas, knock-out au milieu, objectif 3R, mise pour 30 € de risque. Un seul côté par indice, pas d'entrée après 12h, tout fermé à 17h15.
- **17h45** : bilan rejoué de la journée, succès ou échec, cumul dans `reports/matin_journal.csv`.

Simulation et entraînement : la règle de la 1re heure est mesurée dans le rapport du matin, à n'utiliser en réel que si elle est positive. Données Yahoo parfois en retard de 15 min, et GitHub peut lancer la tâche avec 15 à 30 min de retard.
