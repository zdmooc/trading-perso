# Trading perso : scanner de signaux swing

Scanner personnel qui cherche chaque soir des opportunités d'achat swing sur les **5 grands indices mondiaux** (S&P 500, Nasdaq 100, DAX 40, Nikkei 225, FTSE 100) et **15 grandes actions US**, avec entrée, stop, objectif et taille de position. Phase 1 (MVP) : **simulation uniquement, aucun ordre n'est passé**.

> **Avertissement.** Un signal n'est qu'une probabilité, jamais une garantie de gain. Les résultats passés ne préjugent pas des résultats futurs. Outil personnel, pas un conseil en investissement.

## Ce que fait le MVP

| Commande | Rôle |
| --- | --- |
| `tradeperso scan` | Signaux du jour → `reports/signaux.md`, suivi de tous les signaux → `reports/suivi.md` et `reports/journal.csv` (+ alerte Telegram si configurée) |
| `tradeperso backtest --period 10y` | Statistiques de chaque stratégie → `reports/backtest.md` |

Stratégies (bougies journalières, achats uniquement, toutes filtrées par cours > MM200) :

| Stratégie | Entrée | Stop | Sortie |
| --- | --- | --- | --- |
| `tendance_mm` | MM20 croise au-dessus de MM50 | 2 × ATR | objectif 3R (ratio 3,0), ou MM20 repasse sous MM50 |
| `rsi2_repli` | RSI(2) < 10 | 2,5 × ATR | objectif 1,5 ATR (ratio 0,6), ou clôture > MM5 |
| `cassure_20j` | clôture > plus haut 20 jours | 2 × ATR | objectif 2R (ratio 2,0), ou clôture < plus bas 10 jours |

Chaque signal indique son **type** (`swing` pour l'instant ; le day trading arrive en phase 3) et son **ratio gain/perte** = (objectif − entrée) / (entrée − stop).

## Suivi de chaque signal

Chaque signal est inscrit dans `reports/journal.csv` puis suivi chaque soir : entrée à l'ouverture suivante, puis sortie au stop (**échec**), à l'objectif ou sur signal de sortie (**succès** si le résultat est positif). Un signal dont l'ouverture tombe sous le stop est **annulé**. `reports/suivi.md` donne le nombre de succès et d'échecs, le taux de réussite et le résultat cumulé en R, au total et par stratégie ; le message Telegram rappelle le bilan.

## Comment passer un signal

Chaque signal indique :
- **Quand entrer** : à l'ouverture de la séance de Bourse qui suit la clôture du signal (New York 15:30, Francfort et Londres 9:00, Tokyo 1:00 ou 2:00, heure de Paris), au prix du marché. C'est l'ouverture de la Bourse, pas la bougie suivante sur IG ou eToro, qui cotent les indices presque 24 h/24. Les jours fériés ne sont pas encore gérés.
- **Où et quoi** : sur IG, un CFD (indice ou action) ; sur eToro, un CFD pour les indices et une **action réelle sans levier** pour les actions US (pas de frais de nuit).
- **Combien** : la quantité à ACHETER pour perdre environ 1 % du capital si le stop est touché (positions acheteuses uniquement).
- **Ce que ça coûte** : spread + commissions aller-retour et financement par nuit pour les CFD, en euros. Les spreads viennent des pages officielles d'IG et d'eToro (heures principales) ; les taux de financement sont des estimations réglables dans `config.toml`.

Taille de position : `capital × risque_par_trade / (entrée − stop)`, réglable dans [`config.toml`](config.toml) avec la liste des actifs.

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
