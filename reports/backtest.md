# Backtest sur 10y (56 actifs, frais 5 bps, risque 1% par trade)

Ventes à découvert : indices uniquement. Chaque trade est compté sans limite de positions simultanées.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 891 | 28.7 | 0.26 | 1.55 | 772.0 | -31.6 |
| rsi2_repli | 3663 | 63.9 | 0.03 | 1.12 | 138.4 | -65.0 |
| cassure_20j | 2659 | 31.9 | 0.18 | 1.38 | 9042.1 | -49.8 |
| tendance_mm_vente | 26 | 11.5 | -0.21 | 0.58 | -5.4 | -8.6 |
| cassure_20j_vente | 98 | 19.4 | -0.14 | 0.73 | -13.8 | -21.6 |
| repli_tendance (test) | 2208 | 27.1 | 0.14 | 1.36 | 1635.5 | -31.5 |
| repli_tendance_2r (test) | 2395 | 31.3 | 0.11 | 1.3 | 1207.0 | -37.2 |
| repli_tendance_vente (test) | 47 | 23.4 | -0.08 | 0.81 | -4.2 | -9.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1024 | 38.8 | 0.3 | 1.49 | 1683.1 | -37.2 |
| rsi2_repli | 4136 | 64.3 | 0.03 | 1.14 | 205.4 | -65.8 |
| cassure_20j | 2714 | 40.2 | 0.23 | 1.44 | 37651.4 | -50.7 |
| tendance_mm_vente | 52 | 21.2 | -0.27 | 0.65 | -13.7 | -16.8 |
| cassure_20j_vente | 155 | 17.4 | -0.44 | 0.4 | -50.3 | -50.1 |
| repli_tendance (test) | 2258 | 31.7 | 0.12 | 1.28 | 1094.8 | -40.9 |
| repli_tendance_2r (test) | 2471 | 35.4 | 0.11 | 1.28 | 1350.4 | -39.8 |
| repli_tendance_vente (test) | 72 | 16.7 | -0.19 | 0.64 | -13.1 | -21.2 |

## Loi des 20/80 par actif (stratégies envoyées, avec protections)

**24 actifs sur 56 (43 %) font 80 % des gains.**

Stabilité : les 11 meilleurs actifs de la 1re moitié (2022) font +0.18 R par trade dans la 2e moitié, contre +0.16 R pour les autres.

| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Eli Lilly | 61 | +48.1 R | 6 % | +24.4 R | +23.7 R |
| 2 | AMD | 66 | +47.2 R | 13 % | +22.3 R | +24.8 R |
| 3 | Apple | 76 | +42.4 R | 18 % | +37.7 R | +4.6 R |
| 4 | Costco | 71 | +38.2 R | 23 % | +34.0 R | +4.2 R |
| 5 | Caterpillar | 61 | +31.5 R | 27 % | +8.2 R | +23.3 R |
| 6 | Nvidia | 78 | +31.4 R | 32 % | +10.9 R | +20.6 R |
| 7 | S&P 500 | 97 | +29.5 R | 35 % | +15.1 R | +14.4 R |
| 8 | Cisco | 64 | +28.6 R | 39 % | +12.0 R | +16.6 R |
| 9 | Nasdaq 100 | 94 | +28.1 R | 43 % | +7.7 R | +20.4 R |
| 10 | Alphabet | 73 | +26.1 R | 46 % | +13.0 R | +13.1 R |
| 11 | Abbott | 65 | +25.5 R | 50 % | +13.6 R | +11.8 R |
| 12 | Home Depot | 59 | +23.5 R | 53 % | +22.7 R | +0.8 R |
| 13 | Tesla | 68 | +23.0 R | 56 % | +17.5 R | +5.5 R |
| 14 | Berkshire Hathaway | 66 | +21.9 R | 59 % | +17.5 R | +4.4 R |
| 15 | Morgan Stanley | 64 | +21.7 R | 62 % | +6.5 R | +15.2 R |
| 16 | AbbVie | 69 | +18.4 R | 64 % | +16.6 R | +1.9 R |
| 17 | Goldman Sachs | 65 | +18.1 R | 67 % | +6.2 R | +11.8 R |
| 18 | Philip Morris | 55 | +18.0 R | 69 % | +16.8 R | +1.3 R |
| 19 | Amgen | 62 | +17.3 R | 71 % | +9.2 R | +8.1 R |
| 20 | Walmart | 67 | +16.4 R | 73 % | +6.7 R | +9.7 R |
| 21 | Wells Fargo | 52 | +14.1 R | 75 % | +5.2 R | +8.8 R |
| 22 | Adobe | 56 | +13.9 R | 77 % | +20.1 R | -6.3 R |
| 23 | Bank of America | 61 | +13.4 R | 79 % | +3.4 R | +10.0 R |
| 24 | GE Aerospace | 47 | +13.2 R | 81 % | -3.1 R | +16.3 R |
| 25 | JPMorgan | 65 | +12.9 R | 82 % | +3.1 R | +9.8 R |
| 26 | PepsiCo | 56 | +11.7 R | 84 % | +13.6 R | -1.9 R |
| 27 | Microsoft | 75 | +10.3 R | 85 % | +13.1 R | -2.8 R |
| 28 | Mastercard | 65 | +10.0 R | 87 % | +5.2 R | +4.7 R |
| 29 | Visa | 59 | +9.6 R | 88 % | +6.9 R | +2.7 R |
| 30 | Nikkei 225 | 90 | +9.6 R | 89 % | +8.5 R | +1.1 R |
| 31 | Exxon Mobil | 53 | +9.4 R | 90 % | +11.3 R | -1.9 R |
| 32 | Netflix | 62 | +8.8 R | 91 % | +2.2 R | +6.6 R |
| 33 | IBM | 60 | +8.4 R | 93 % | -2.2 R | +10.6 R |
| 34 | Uber | 39 | +7.3 R | 94 % | -0.8 R | +8.1 R |
| 35 | Thermo Fisher | 63 | +7.3 R | 95 % | +16.7 R | -9.4 R |
| 36 | Intel | 56 | +7.2 R | 95 % | -5.6 R | +12.8 R |
| 37 | McDonald's | 57 | +5.8 R | 96 % | +7.2 R | -1.4 R |
| 38 | Qualcomm | 66 | +5.7 R | 97 % | +9.0 R | -3.4 R |
| 39 | Coca-Cola | 63 | +5.3 R | 98 % | +4.2 R | +1.1 R |
| 40 | Intuit | 63 | +4.0 R | 98 % | +12.7 R | -8.7 R |
| 41 | Broadcom | 71 | +3.5 R | 99 % | -3.4 R | +6.8 R |
| 42 | UnitedHealth | 59 | +2.4 R | 99 % | +1.7 R | +0.7 R |
| 43 | Salesforce | 64 | +2.4 R | 99 % | -3.8 R | +6.2 R |
| 44 | ServiceNow | 63 | +2.3 R | 100 % | +1.2 R | +1.1 R |
| 45 | Disney | 46 | +2.2 R | 100 % | +0.6 R | +1.6 R |
| 46 | Meta | 64 | +0.5 R | 100 % | -7.5 R | +7.9 R |
| 47 | Procter & Gamble | 58 | +0.4 R | 100 % | +4.5 R | -4.2 R |
| 48 | Merck | 57 | -0.9 R | 100 % | -5.3 R | +4.4 R |
| 49 | Amazon | 72 | -2.1 R | 100 % | +2.8 R | -4.9 R |
| 50 | Johnson & Johnson | 67 | -2.4 R | 100 % | -1.5 R | -0.9 R |
| 51 | Oracle | 67 | -5.0 R | 100 % | -13.8 R | +8.8 R |
| 52 | Texas Instruments | 75 | -5.8 R | 100 % | +1.4 R | -7.2 R |
| 53 | Chevron | 63 | -6.0 R | 100 % | +1.5 R | -7.5 R |
| 54 | DAX 40 | 88 | -9.5 R | 100 % | -3.8 R | -5.8 R |
| 55 | CAC 40 | 81 | -10.0 R | 100 % | +6.7 R | -16.7 R |
| 56 | FTSE 100 | 90 | -21.8 R | 100 % | -12.2 R | -9.7 R |

Résultats passés : aucune garantie pour l'avenir.
