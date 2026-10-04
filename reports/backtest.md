# Backtest sur 10y (57 actifs, frais 5 bps, risque 1% par trade)

## Résultat réaliste du portefeuille (stratégies actives, 4 positions au maximum)

**+8.5 % par an** (+120.0 % au total), pire baisse **-23.8 %**, plus longue période sous un ancien sommet : 38.5 mois.

| Trades | Réussite | Gain moyen | Perte moyenne | Espérance par trade | Profit factor |
| --- | --- | --- | --- | --- | --- |
| 547 | 30.0 % | +2.04 R | -0.64 R | +0.16 R | 1.37 |

Par stratégie : cassure_20j 209 trades (+36.7 R), cassure_20j_vente 69 trades (-4.0 R), repli_tendance 193 trades (+15.7 R), tendance_mm 67 trades (+42.3 R), tendance_mm_vente 9 trades (-0.5 R).

### Comparaison avec « acheter et garder » (02/2017 à 10/2026)

| Méthode | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| **Ce système** (4 positions, risque 1% par trade) | +8.5 % | +120.0 % | -23.8 % | 38.5 mois |
| Garder le S&P 500 (ETF SPY, dividendes inclus) | +15.2 % | +293.6 % | -33.7 % | 23.2 mois |
| Garder le Nasdaq 100 (ETF QQQ, dividendes inclus) | +21.1 % | +537.6 % | -35.1 % | 23.5 mois |
| Garder Apple, Microsoft, Alphabet, Amazon, Meta et Nvidia (parts égales) | +36.8 % | +1966.9 % | -46.6 % | 18.1 mois |

### Spéculation : rotation sur les actions leaders (actions réelles, parts égales)

| Variante | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| Avec filtre de marché | +14.1 % | +250.7 % | -28.8 % | 22.3 mois |
| Sans filtre de marché | +20.6 % | +491.0 % | -39.4 % | 18.4 mois |

⚠️ Biais : la liste contient les grandes actions d'aujourd'hui, donc des gagnantes connues après coup. Le résultat réel sera plus faible.


## Solidité des réglages

Si un petit changement de réglage fait s'effondrer le résultat, la stratégie est trop ajustée au passé.

| Variante | Trades | Espérance par trade | Rendement par an | Pire baisse |
| --- | --- | --- | --- | --- |
| Réglage actuel | 547 | +0.16 R | +8.5 % | -23.8 % |
| Cassure sur 15 jours | 557 | +0.13 R | +6.3 % | -28.2 % |
| Cassure sur 25 jours | 553 | +0.16 R | +8.3 % | -28.4 % |
| Moyenne longue 150 jours | 556 | +0.18 R | +9.7 % | -24.3 % |
| Moyenne longue 250 jours | 562 | +0.22 R | +12.4 % | -21.6 % |
| Stop à 1,5 ATR | 697 | +0.16 R | +10.3 % | -26.7 % |
| Stop à 2,5 ATR | 451 | +0.18 R | +7.9 % | -15.2 % |
| Sans stop au prix d'entrée | 521 | +0.12 R | +5.4 % | -20.2 % |
| Sans filtre de marché | 625 | +0.24 R | +14.5 % | -26.4 % |

# Détail par stratégie (trades indépendants)

Ventes à découvert : indices uniquement. Ici, chaque trade est compté sans limite de positions simultanées : les rendements sont donc gonflés. Seuls le gain moyen (R) et le profit factor se comparent.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 892 | 28.8 | 0.26 | 1.56 | 805.7 | -31.6 |
| rsi2_repli | 3662 | 63.8 | 0.03 | 1.12 | 136.9 | -65.2 |
| cassure_20j | 2658 | 31.9 | 0.18 | 1.39 | 9600.5 | -49.3 |
| tendance_mm_vente | 34 | 11.8 | -0.36 | 0.39 | -11.6 | -10.6 |
| cassure_20j_vente | 106 | 19.8 | -0.17 | 0.68 | -17.6 | -21.6 |
| repli_tendance | 2209 | 27.1 | 0.14 | 1.37 | 1686.2 | -31.3 |
| repli_tendance_2r (test) | 2396 | 31.3 | 0.11 | 1.31 | 1228.4 | -37.0 |
| repli_tendance_vente (test) | 47 | 23.4 | -0.08 | 0.81 | -4.2 | -9.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1092 | 39.7 | 0.35 | 1.58 | 3520.7 | -37.2 |
| rsi2_repli | 4135 | 64.3 | 0.03 | 1.14 | 203.5 | -65.9 |
| cassure_20j | 2928 | 40.9 | 0.26 | 1.5 | 139205.8 | -50.7 |
| tendance_mm_vente | 60 | 20.0 | -0.35 | 0.55 | -19.7 | -18.8 |
| cassure_20j_vente | 162 | 17.9 | -0.45 | 0.39 | -52.1 | -51.6 |
| repli_tendance | 2258 | 31.7 | 0.12 | 1.28 | 1117.5 | -40.9 |
| repli_tendance_2r (test) | 2471 | 35.3 | 0.12 | 1.28 | 1355.9 | -39.9 |
| repli_tendance_vente (test) | 72 | 16.7 | -0.19 | 0.64 | -13.1 | -21.2 |

## Day trading en barrières IG (indices, cassure du plus haut ou du plus bas de la veille)

Un trade par jour au plus, clôture en fin de séance. Si le stop et l'objectif sont touchés le même jour, le stop est compté (hypothèse prudente).

| Filtre de la veille | Sens | Knock-out | Trades | Réussite | Espérance par trade | Profit factor | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tous | deux_sens | 0.5 ATR | 12075 | 33.5 % | -0.341 R | 0.42 | -4114.1 R |
| tous | deux_sens | 1.0 ATR | 12075 | 43.8 % | -0.062 R | 0.73 | -753.3 R |
| tous | tendance | 0.5 ATR | 6953 | 33.4 % | -0.344 R | 0.41 | -2390.3 R |
| tous | tendance | 1.0 ATR | 6953 | 42.9 % | -0.083 R | 0.67 | -574.1 R |
| nr4 ⬅ | deux_sens | 0.5 ATR | 3575 | 35.6 % | -0.277 R | 0.48 | -988.7 R |
| nr4 | deux_sens | 1.0 ATR | 3575 | 43.9 % | -0.04 R | 0.8 | -141.7 R |
| nr4 | tendance | 0.5 ATR | 2028 | 35.3 % | -0.304 R | 0.44 | -616.4 R |
| nr4 | tendance | 1.0 ATR | 2028 | 42.9 % | -0.071 R | 0.69 | -144.1 R |
| inside | deux_sens | 0.5 ATR | 1525 | 33.6 % | -0.343 R | 0.41 | -522.9 R |
| inside | deux_sens | 1.0 ATR | 1525 | 43.3 % | -0.077 R | 0.68 | -116.9 R |
| inside | tendance | 0.5 ATR | 845 | 30.9 % | -0.425 R | 0.33 | -359.3 R |
| inside | tendance | 1.0 ATR | 845 | 40.9 % | -0.138 R | 0.5 | -116.7 R |

Par indice (réglage actuel ⬅) :

| Indice | Trades | Espérance par trade | Total |
| --- | --- | --- | --- |
| S&P 500 | 623 | -0.241 R | -150.2 R |
| Nasdaq 100 | 602 | -0.263 R | -158.5 R |
| DAX 40 | 581 | -0.304 R | -176.5 R |
| Nikkei 225 | 603 | -0.157 R | -94.4 R |
| FTSE 100 | 565 | -0.358 R | -202.1 R |
| CAC 40 | 601 | -0.344 R | -207.0 R |

## Loi des 20/80 par actif (stratégies envoyées, avec protections)

**25 actifs sur 56 (45 %) font 80 % des gains.**

Stabilité : les 11 meilleurs actifs de la 1re moitié (2021) font +0.15 R par trade dans la 2e moitié, contre +0.13 R pour les autres.

| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Apple | 113 | +55.9 R | 5 % | +45.7 R | +10.3 R |
| 2 | AMD | 103 | +55.7 R | 10 % | +30.3 R | +25.4 R |
| 3 | Caterpillar | 92 | +50.2 R | 14 % | +17.7 R | +32.5 R |
| 4 | Costco | 116 | +50.2 R | 19 % | +45.8 R | +4.3 R |
| 5 | Alphabet | 119 | +48.1 R | 23 % | +28.3 R | +19.7 R |
| 6 | Nasdaq 100 | 141 | +47.6 R | 27 % | +24.2 R | +23.4 R |
| 7 | Nvidia | 132 | +45.5 R | 31 % | +21.4 R | +24.2 R |
| 8 | S&P 500 | 142 | +44.4 R | 35 % | +26.8 R | +17.6 R |
| 9 | Eli Lilly | 96 | +42.5 R | 39 % | +23.7 R | +18.8 R |
| 10 | Cisco | 104 | +40.1 R | 42 % | +15.7 R | +24.4 R |
| 11 | Tesla | 94 | +36.1 R | 45 % | +32.3 R | +3.8 R |
| 12 | Home Depot | 88 | +35.6 R | 48 % | +33.1 R | +2.5 R |
| 13 | Berkshire Hathaway | 101 | +34.8 R | 52 % | +16.0 R | +18.8 R |
| 14 | Morgan Stanley | 101 | +34.6 R | 55 % | +17.7 R | +16.8 R |
| 15 | Goldman Sachs | 104 | +32.6 R | 57 % | +7.8 R | +24.8 R |
| 16 | Mastercard | 104 | +32.5 R | 60 % | +23.1 R | +9.5 R |
| 17 | Walmart | 111 | +31.4 R | 63 % | +17.7 R | +13.6 R |
| 18 | Microsoft | 131 | +30.1 R | 66 % | +31.3 R | -1.1 R |
| 19 | JPMorgan | 103 | +30.1 R | 68 % | +8.8 R | +21.3 R |
| 20 | Abbott | 116 | +26.8 R | 71 % | +19.1 R | +7.7 R |
| 21 | AbbVie | 105 | +24.5 R | 73 % | +13.4 R | +11.1 R |
| 22 | Adobe | 93 | +23.7 R | 75 % | +32.3 R | -8.6 R |
| 23 | GE Aerospace | 84 | +23.1 R | 77 % | -3.5 R | +26.6 R |
| 24 | Amgen | 96 | +23.1 R | 79 % | +13.1 R | +10.0 R |
| 25 | Salesforce | 97 | +22.5 R | 81 % | +10.3 R | +12.2 R |
| 26 | McDonald's | 93 | +18.8 R | 83 % | +22.3 R | -3.4 R |
| 27 | Visa | 103 | +14.5 R | 84 % | +12.1 R | +2.4 R |
| 28 | Wells Fargo | 87 | +14.3 R | 85 % | +10.4 R | +4.0 R |
| 29 | PepsiCo | 89 | +13.5 R | 86 % | +15.8 R | -2.3 R |
| 30 | IBM | 85 | +13.3 R | 87 % | -5.4 R | +18.7 R |
| 31 | Philip Morris | 81 | +12.5 R | 89 % | +8.1 R | +4.4 R |
| 32 | Coca-Cola | 101 | +12.3 R | 90 % | +8.5 R | +3.8 R |
| 33 | Intel | 82 | +12.3 R | 91 % | -4.5 R | +16.8 R |
| 34 | Nikkei 225 | 141 | +12.2 R | 92 % | +8.8 R | +3.3 R |
| 35 | Netflix | 103 | +11.9 R | 93 % | +4.5 R | +7.3 R |
| 36 | Bank of America | 99 | +11.8 R | 94 % | +3.4 R | +8.4 R |
| 37 | Broadcom | 135 | +11.5 R | 95 % | -6.9 R | +18.4 R |
| 38 | Uber | 68 | +10.9 R | 96 % | +2.2 R | +8.7 R |
| 39 | Intuit | 110 | +10.6 R | 97 % | +26.2 R | -15.6 R |
| 40 | Qualcomm | 93 | +10.0 R | 98 % | +9.7 R | +0.3 R |
| 41 | Thermo Fisher | 108 | +9.4 R | 98 % | +22.3 R | -12.9 R |
| 42 | ServiceNow | 116 | +8.7 R | 99 % | +7.2 R | +1.5 R |
| 43 | Exxon Mobil | 93 | +4.6 R | 100 % | +5.9 R | -1.3 R |
| 44 | Disney | 66 | +4.2 R | 100 % | -2.3 R | +6.5 R |
| 45 | Merck | 93 | -0.7 R | 100 % | -5.2 R | +4.5 R |
| 46 | UnitedHealth | 95 | -1.2 R | 100 % | -1.2 R | -0.0 R |
| 47 | Procter & Gamble | 93 | -2.6 R | 100 % | +5.3 R | -7.9 R |
| 48 | Amazon | 114 | -3.1 R | 100 % | +3.5 R | -6.6 R |
| 49 | Johnson & Johnson | 104 | -3.1 R | 100 % | -5.6 R | +2.4 R |
| 50 | Meta | 109 | -5.8 R | 100 % | -15.8 R | +10.1 R |
| 51 | Chevron | 95 | -8.2 R | 100 % | -1.7 R | -6.5 R |
| 52 | Oracle | 105 | -10.9 R | 100 % | -13.0 R | +2.1 R |
| 53 | DAX 40 | 144 | -19.5 R | 100 % | -6.1 R | -13.3 R |
| 54 | Texas Instruments | 134 | -22.4 R | 100 % | -9.5 R | -12.9 R |
| 55 | CAC 40 | 132 | -26.7 R | 100 % | -1.7 R | -25.0 R |
| 56 | FTSE 100 | 142 | -37.1 R | 100 % | -24.7 R | -12.3 R |

Résultats passés : aucune garantie pour l'avenir.
