# Backtest sur 10y (56 actifs, frais 5 bps, risque 1% par trade)

## Résultat réaliste du portefeuille (stratégies actives, 4 positions au maximum)

**+10.1 % par an** (+143.1 % au total), pire baisse **-23.8 %**, plus longue période sous un ancien sommet : 38.5 mois.

| Trades | Réussite | Gain moyen | Perte moyenne | Espérance par trade | Profit factor |
| --- | --- | --- | --- | --- | --- |
| 539 | 29.9 % | +2.08 R | -0.62 R | +0.19 R | 1.43 |

Par stratégie : cassure_20j 209 trades (+42.6 R), cassure_20j_vente 62 trades (+0.4 R), repli_tendance 196 trades (+16.0 R), tendance_mm 66 trades (+39.7 R), tendance_mm_vente 6 trades (+1.5 R).

## Solidité des réglages

Si un petit changement de réglage fait s'effondrer le résultat, la stratégie est trop ajustée au passé.

| Variante | Trades | Espérance par trade | Rendement par an | Pire baisse |
| --- | --- | --- | --- | --- |
| Réglage actuel | 539 | +0.19 R | +10.1 % | -23.8 % |
| Cassure sur 15 jours | 555 | +0.15 R | +7.9 % | -28.2 % |
| Cassure sur 25 jours | 549 | +0.18 R | +9.9 % | -28.4 % |
| Moyenne longue 150 jours | 551 | +0.19 R | +10.5 % | -24.3 % |
| Moyenne longue 250 jours | 549 | +0.24 R | +14.2 % | -21.6 % |
| Stop à 1,5 ATR | 694 | +0.16 R | +11.0 % | -26.7 % |
| Stop à 2,5 ATR | 443 | +0.2 R | +9.3 % | -15.2 % |
| Sans stop au prix d'entrée | 509 | +0.13 R | +6.2 % | -21.1 % |
| Sans filtre de marché | 590 | +0.23 R | +14.0 % | -26.4 % |

# Détail par stratégie (trades indépendants)

Ventes à découvert : indices uniquement. Ici, chaque trade est compté sans limite de positions simultanées : les rendements sont donc gonflés. Seuls le gain moyen (R) et le profit factor se comparent.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 891 | 28.7 | 0.26 | 1.55 | 772.0 | -31.6 |
| rsi2_repli | 3662 | 63.8 | 0.03 | 1.12 | 137.5 | -65.2 |
| cassure_20j | 2657 | 31.9 | 0.18 | 1.38 | 8895.3 | -49.8 |
| tendance_mm_vente | 26 | 11.5 | -0.21 | 0.58 | -5.4 | -8.6 |
| cassure_20j_vente | 98 | 19.4 | -0.14 | 0.73 | -13.8 | -21.6 |
| repli_tendance | 2208 | 27.1 | 0.14 | 1.37 | 1674.1 | -31.3 |
| repli_tendance_2r (test) | 2395 | 31.3 | 0.11 | 1.31 | 1235.6 | -37.2 |
| repli_tendance_vente (test) | 47 | 23.4 | -0.08 | 0.81 | -4.2 | -9.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1024 | 38.8 | 0.3 | 1.49 | 1683.2 | -37.2 |
| rsi2_repli | 4135 | 64.3 | 0.03 | 1.14 | 204.2 | -65.9 |
| cassure_20j | 2712 | 40.2 | 0.23 | 1.44 | 37881.4 | -50.3 |
| tendance_mm_vente | 52 | 21.2 | -0.27 | 0.65 | -13.7 | -16.8 |
| cassure_20j_vente | 155 | 17.4 | -0.44 | 0.4 | -50.3 | -50.1 |
| repli_tendance | 2258 | 31.7 | 0.12 | 1.28 | 1100.0 | -40.9 |
| repli_tendance_2r (test) | 2471 | 35.3 | 0.12 | 1.28 | 1356.7 | -39.9 |
| repli_tendance_vente (test) | 72 | 16.7 | -0.19 | 0.64 | -13.1 | -21.2 |

## Loi des 20/80 par actif (stratégies envoyées, avec protections)

**25 actifs sur 56 (45 %) font 80 % des gains.**

Stabilité : les 11 meilleurs actifs de la 1re moitié (2022) font +0.15 R par trade dans la 2e moitié, contre +0.15 R pour les autres.

| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AMD | 103 | +55.7 R | 5 % | +29.6 R | +26.1 R |
| 2 | Apple | 114 | +55.5 R | 10 % | +47.7 R | +7.9 R |
| 3 | Caterpillar | 92 | +50.2 R | 14 % | +17.6 R | +32.6 R |
| 4 | Costco | 116 | +50.2 R | 19 % | +42.8 R | +7.4 R |
| 5 | Nasdaq 100 | 139 | +49.8 R | 23 % | +23.7 R | +26.1 R |
| 6 | Alphabet | 119 | +48.1 R | 27 % | +24.1 R | +24.0 R |
| 7 | Nvidia | 132 | +45.5 R | 31 % | +19.8 R | +25.7 R |
| 8 | S&P 500 | 141 | +45.4 R | 35 % | +24.5 R | +21.0 R |
| 9 | Eli Lilly | 96 | +42.5 R | 39 % | +22.2 R | +20.3 R |
| 10 | Tesla | 94 | +36.1 R | 42 % | +29.6 R | +6.5 R |
| 11 | Morgan Stanley | 100 | +35.7 R | 45 % | +12.7 R | +23.0 R |
| 12 | Home Depot | 88 | +35.6 R | 49 % | +32.4 R | +3.2 R |
| 13 | Cisco | 104 | +35.1 R | 52 % | +10.7 R | +24.3 R |
| 14 | Berkshire Hathaway | 101 | +34.8 R | 55 % | +23.4 R | +11.4 R |
| 15 | Goldman Sachs | 104 | +32.6 R | 58 % | +6.7 R | +26.0 R |
| 16 | Mastercard | 105 | +31.9 R | 60 % | +20.0 R | +12.0 R |
| 17 | Walmart | 111 | +30.4 R | 63 % | +16.4 R | +14.0 R |
| 18 | JPMorgan | 103 | +30.1 R | 66 % | +7.8 R | +22.3 R |
| 19 | Microsoft | 131 | +29.1 R | 68 % | +29.0 R | +0.1 R |
| 20 | Abbott | 116 | +26.8 R | 71 % | +19.5 R | +7.3 R |
| 21 | AbbVie | 105 | +24.5 R | 73 % | +24.1 R | +0.4 R |
| 22 | Adobe | 93 | +23.7 R | 75 % | +31.3 R | -7.6 R |
| 23 | GE Aerospace | 83 | +23.5 R | 77 % | -3.1 R | +26.6 R |
| 24 | Amgen | 96 | +23.1 R | 79 % | +11.0 R | +12.0 R |
| 25 | Salesforce | 97 | +22.5 R | 81 % | +10.3 R | +12.2 R |
| 26 | McDonald's | 93 | +18.8 R | 83 % | +22.3 R | -3.5 R |
| 27 | Wells Fargo | 87 | +14.3 R | 84 % | +6.0 R | +8.4 R |
| 28 | Visa | 103 | +14.2 R | 85 % | +11.0 R | +3.2 R |
| 29 | IBM | 85 | +13.9 R | 86 % | -4.8 R | +18.7 R |
| 30 | Bank of America | 98 | +13.9 R | 88 % | +3.8 R | +10.1 R |
| 31 | Nikkei 225 | 138 | +13.6 R | 89 % | +7.5 R | +6.0 R |
| 32 | PepsiCo | 89 | +13.5 R | 90 % | +15.9 R | -2.4 R |
| 33 | Philip Morris | 81 | +12.5 R | 91 % | +13.0 R | -0.4 R |
| 34 | Intel | 82 | +12.3 R | 92 % | -4.5 R | +16.8 R |
| 35 | Netflix | 103 | +11.9 R | 93 % | +4.5 R | +7.3 R |
| 36 | Broadcom | 135 | +11.5 R | 94 % | -2.6 R | +14.1 R |
| 37 | Coca-Cola | 102 | +11.3 R | 95 % | +7.5 R | +3.8 R |
| 38 | Intuit | 110 | +10.6 R | 96 % | +24.7 R | -14.1 R |
| 39 | Qualcomm | 93 | +10.0 R | 97 % | +12.2 R | -2.2 R |
| 40 | Thermo Fisher | 108 | +9.4 R | 98 % | +22.9 R | -13.5 R |
| 41 | ServiceNow | 116 | +8.7 R | 99 % | +6.0 R | +2.7 R |
| 42 | Uber | 64 | +5.2 R | 99 % | -3.5 R | +8.7 R |
| 43 | Exxon Mobil | 93 | +4.6 R | 100 % | +9.9 R | -5.2 R |
| 44 | Disney | 66 | +4.2 R | 100 % | -2.3 R | +6.5 R |
| 45 | Merck | 93 | -0.7 R | 100 % | -6.2 R | +5.5 R |
| 46 | UnitedHealth | 95 | -1.2 R | 100 % | +0.3 R | -1.6 R |
| 47 | Procter & Gamble | 93 | -2.6 R | 100 % | +8.2 R | -10.8 R |
| 48 | Amazon | 114 | -3.1 R | 100 % | +3.5 R | -6.6 R |
| 49 | Johnson & Johnson | 104 | -3.1 R | 100 % | -6.0 R | +2.9 R |
| 50 | Meta | 109 | -5.8 R | 100 % | -17.8 R | +12.1 R |
| 51 | Chevron | 95 | -8.2 R | 100 % | +1.4 R | -9.6 R |
| 52 | Oracle | 106 | -12.4 R | 100 % | -15.2 R | +2.8 R |
| 53 | DAX 40 | 142 | -19.0 R | 100 % | -8.5 R | -10.5 R |
| 54 | Texas Instruments | 134 | -22.4 R | 100 % | -11.4 R | -11.0 R |
| 55 | CAC 40 | 128 | -24.8 R | 100 % | -1.3 R | -23.4 R |
| 56 | FTSE 100 | 138 | -33.0 R | 100 % | -25.3 R | -7.7 R |

Résultats passés : aucune garantie pour l'avenir.
