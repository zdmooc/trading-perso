# Backtest sur 10y (56 actifs, frais 5 bps, risque 1% par trade)

Ventes à découvert : indices uniquement. Chaque trade est compté sans limite de positions simultanées.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 891 | 28.7 | 0.26 | 1.55 | 772.0 | -31.6 |
| rsi2_repli | 3662 | 63.8 | 0.03 | 1.12 | 137.5 | -65.2 |
| cassure_20j | 2655 | 31.9 | 0.18 | 1.38 | 9045.1 | -49.3 |
| tendance_mm_vente | 26 | 11.5 | -0.21 | 0.58 | -5.4 | -8.6 |
| cassure_20j_vente | 98 | 19.4 | -0.14 | 0.73 | -13.8 | -21.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1024 | 38.8 | 0.3 | 1.49 | 1683.1 | -37.2 |
| rsi2_repli | 4135 | 64.3 | 0.03 | 1.14 | 204.2 | -65.9 |
| cassure_20j | 2710 | 40.2 | 0.23 | 1.44 | 37716.7 | -50.3 |
| tendance_mm_vente | 52 | 21.2 | -0.27 | 0.65 | -13.7 | -16.8 |
| cassure_20j_vente | 155 | 17.4 | -0.44 | 0.4 | -50.3 | -50.1 |

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
| 6 | Nvidia | 78 | +31.5 R | 32 % | +10.9 R | +20.6 R |
| 7 | S&P 500 | 97 | +29.5 R | 35 % | +15.1 R | +14.4 R |
| 8 | Nasdaq 100 | 94 | +28.1 R | 39 % | +7.7 R | +20.4 R |
| 9 | Cisco | 64 | +26.1 R | 43 % | +9.6 R | +16.6 R |
| 10 | Alphabet | 73 | +26.1 R | 46 % | +13.0 R | +13.1 R |
| 11 | Abbott | 65 | +25.5 R | 49 % | +13.6 R | +11.8 R |
| 12 | Morgan Stanley | 62 | +23.9 R | 53 % | +7.7 R | +16.2 R |
| 13 | Home Depot | 59 | +23.5 R | 56 % | +22.7 R | +0.8 R |
| 14 | Tesla | 68 | +23.0 R | 59 % | +17.5 R | +5.5 R |
| 15 | Berkshire Hathaway | 66 | +21.9 R | 62 % | +17.5 R | +4.4 R |
| 16 | AbbVie | 69 | +18.3 R | 64 % | +16.5 R | +1.9 R |
| 17 | Goldman Sachs | 65 | +18.1 R | 66 % | +6.2 R | +11.8 R |
| 18 | Philip Morris | 55 | +18.0 R | 69 % | +16.8 R | +1.3 R |
| 19 | Walmart | 67 | +17.4 R | 71 % | +6.7 R | +10.7 R |
| 20 | Amgen | 62 | +17.3 R | 73 % | +9.2 R | +8.1 R |
| 21 | Wells Fargo | 52 | +14.1 R | 75 % | +5.2 R | +8.8 R |
| 22 | Adobe | 56 | +13.9 R | 77 % | +20.1 R | -6.3 R |
| 23 | Bank of America | 61 | +13.4 R | 79 % | +3.4 R | +10.0 R |
| 24 | GE Aerospace | 47 | +13.2 R | 81 % | -3.1 R | +16.3 R |
| 25 | JPMorgan | 65 | +12.9 R | 82 % | +3.1 R | +9.8 R |
| 26 | PepsiCo | 56 | +11.7 R | 84 % | +13.6 R | -1.9 R |
| 27 | Microsoft | 75 | +11.3 R | 85 % | +14.2 R | -2.8 R |
| 28 | Mastercard | 65 | +10.0 R | 87 % | +5.2 R | +4.7 R |
| 29 | Nikkei 225 | 90 | +9.6 R | 88 % | +8.5 R | +1.1 R |
| 30 | Exxon Mobil | 53 | +9.4 R | 89 % | +11.3 R | -1.9 R |
| 31 | Visa | 59 | +9.2 R | 90 % | +6.5 R | +2.7 R |
| 32 | Netflix | 62 | +8.8 R | 92 % | +2.2 R | +6.6 R |
| 33 | IBM | 60 | +7.7 R | 93 % | -2.9 R | +10.6 R |
| 34 | Uber | 39 | +7.3 R | 94 % | -0.8 R | +8.1 R |
| 35 | Thermo Fisher | 63 | +7.3 R | 95 % | +16.7 R | -9.4 R |
| 36 | Intel | 56 | +7.2 R | 95 % | -5.6 R | +12.8 R |
| 37 | Coca-Cola | 62 | +6.3 R | 96 % | +5.2 R | +1.1 R |
| 38 | McDonald's | 57 | +5.8 R | 97 % | +7.2 R | -1.4 R |
| 39 | Qualcomm | 66 | +4.4 R | 98 % | +9.0 R | -4.6 R |
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
| 51 | Oracle | 66 | -5.4 R | 100 % | -15.2 R | +9.8 R |
| 52 | Texas Instruments | 75 | -5.8 R | 100 % | +1.4 R | -7.2 R |
| 53 | Chevron | 63 | -6.0 R | 100 % | +1.5 R | -7.5 R |
| 54 | DAX 40 | 88 | -9.5 R | 100 % | -3.8 R | -5.8 R |
| 55 | CAC 40 | 81 | -10.0 R | 100 % | +6.7 R | -16.7 R |
| 56 | FTSE 100 | 90 | -21.8 R | 100 % | -12.2 R | -9.7 R |

Résultats passés : aucune garantie pour l'avenir.
