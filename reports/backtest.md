# Backtest sur 10y (56 actifs, frais 5 bps, risque 1% par trade)

Ventes à découvert : indices uniquement. Chaque trade est compté sans limite de positions simultanées.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 891 | 28.7 | 0.26 | 1.55 | 772.0 | -31.6 |
| rsi2_repli | 3663 | 63.9 | 0.03 | 1.12 | 138.6 | -65.1 |
| cassure_20j | 2656 | 31.9 | 0.18 | 1.38 | 9050.3 | -49.3 |
| tendance_mm_vente | 26 | 11.5 | -0.21 | 0.58 | -5.4 | -8.6 |
| cassure_20j_vente | 98 | 19.4 | -0.14 | 0.73 | -13.8 | -21.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1024 | 38.8 | 0.3 | 1.49 | 1683.1 | -37.2 |
| rsi2_repli | 4136 | 64.3 | 0.03 | 1.14 | 205.8 | -65.8 |
| cassure_20j | 2711 | 40.2 | 0.23 | 1.44 | 37692.7 | -50.9 |
| tendance_mm_vente | 52 | 21.2 | -0.27 | 0.65 | -13.7 | -16.8 |
| cassure_20j_vente | 155 | 17.4 | -0.44 | 0.4 | -50.3 | -50.1 |

Résultats passés : aucune garantie pour l'avenir.
