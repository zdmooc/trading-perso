# Trading perso : scanner de signaux swing

Scanner personnel qui cherche chaque soir des opportunités d'achat swing sur les **5 grands indices mondiaux** (S&P 500, Nasdaq 100, DAX 40, Nikkei 225, FTSE 100) et **15 grandes actions US**, avec entrée, stop, objectif et taille de position. Phase 1 (MVP) : **simulation uniquement, aucun ordre n'est passé**.

> **Avertissement.** Un signal n'est qu'une probabilité, jamais une garantie de gain. Les résultats passés ne préjugent pas des résultats futurs. Outil personnel, pas un conseil en investissement.

## Ce que fait le MVP

| Commande | Rôle |
| --- | --- |
| `tradeperso scan` | Signaux du jour → `reports/signaux.md` (+ alerte Telegram si configurée) |
| `tradeperso backtest --period 10y` | Statistiques de chaque stratégie → `reports/backtest.md` |

Stratégies (bougies journalières, achats uniquement, toutes filtrées par cours > MM200) :

| Stratégie | Entrée | Stop | Sortie |
| --- | --- | --- | --- |
| `tendance_mm` | MM20 croise au-dessus de MM50 | 2 × ATR | MM20 repasse sous MM50 |
| `rsi2_repli` | RSI(2) < 10 | 2,5 × ATR | clôture > MM5 |
| `cassure_20j` | clôture > plus haut 20 jours | 2 × ATR | objectif 2R, ou clôture < plus bas 10 jours |

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
