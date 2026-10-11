# Backtest sur 10y (57 actifs, frais 5 bps, risque 1% par trade)

## Résultat réaliste du portefeuille (stratégies actives, 4 positions au maximum)

**+8.3 % par an** (+117.1 % au total), pire baisse **-23.8 %**, plus longue période sous un ancien sommet : 38.5 mois.

| Trades | Réussite | Gain moyen | Perte moyenne | Espérance par trade | Profit factor |
| --- | --- | --- | --- | --- | --- |
| 547 | 30.0 % | +2.0 R | -0.62 R | +0.16 R | 1.37 |

Par stratégie : cassure_20j 217 trades (+40.2 R), cassure_20j_vente 69 trades (-4.0 R), repli_tendance 184 trades (+15.1 R), tendance_mm 68 trades (+37.6 R), tendance_mm_vente 9 trades (-0.5 R).

### Comparaison avec « acheter et garder » (02/2017 à 10/2026)

| Méthode | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| **Ce système** (4 positions, risque 1% par trade) | +8.3 % | +117.1 % | -23.8 % | 38.5 mois |
| Garder le S&P 500 (ETF SPY, dividendes inclus) | +15.3 % | +298.2 % | -33.7 % | 23.2 mois |
| Garder le Nasdaq 100 (ETF QQQ, dividendes inclus) | +21.1 % | +539.0 % | -35.1 % | 23.5 mois |
| Garder Apple, Microsoft, Alphabet, Amazon, Meta et Nvidia (parts égales) | +36.6 % | +1952.4 % | -46.6 % | 18.1 mois |

### Spéculation : rotation sur les actions leaders (actions réelles, parts égales)

| Variante | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| Avec filtre de marché | +13.7 % | +238.3 % | -28.8 % | 22.3 mois |
| Sans filtre de marché | +20.0 % | +466.4 % | -39.4 % | 18.4 mois |

⚠️ Biais : la liste contient les grandes actions d'aujourd'hui, donc des gagnantes connues après coup. Le résultat réel sera plus faible.


## Solidité des réglages

Si un petit changement de réglage fait s'effondrer le résultat, la stratégie est trop ajustée au passé.

| Variante | Trades | Espérance par trade | Rendement par an | Pire baisse |
| --- | --- | --- | --- | --- |
| Réglage actuel | 547 | +0.16 R | +8.3 % | -23.8 % |
| Cassure sur 15 jours | 563 | +0.11 R | +5.3 % | -28.2 % |
| Cassure sur 25 jours | 552 | +0.17 R | +8.8 % | -28.4 % |
| Moyenne longue 150 jours | 558 | +0.18 R | +9.5 % | -24.3 % |
| Moyenne longue 250 jours | 562 | +0.22 R | +12.1 % | -21.6 % |
| Stop à 1,5 ATR | 699 | +0.15 R | +9.6 % | -26.7 % |
| Stop à 2,5 ATR | 453 | +0.19 R | +8.6 % | -15.2 % |
| Sans stop au prix d'entrée | 524 | +0.12 R | +5.8 % | -20.2 % |
| Sans filtre de marché | 619 | +0.26 R | +15.6 % | -26.4 % |

# Détail par stratégie (trades indépendants)

Ventes à découvert : indices uniquement. Ici, chaque trade est compté sans limite de positions simultanées : les rendements sont donc gonflés. Seuls le gain moyen (R) et le profit factor se comparent.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 893 | 28.8 | 0.26 | 1.56 | 805.8 | -31.6 |
| rsi2_repli | 3670 | 64.0 | 0.03 | 1.12 | 138.6 | -65.0 |
| cassure_20j | 2655 | 31.9 | 0.18 | 1.39 | 9459.4 | -49.3 |
| tendance_mm_vente | 34 | 11.8 | -0.36 | 0.39 | -11.6 | -10.6 |
| cassure_20j_vente | 106 | 19.8 | -0.17 | 0.68 | -17.6 | -21.6 |
| repli_tendance | 2197 | 27.2 | 0.14 | 1.38 | 1840.3 | -30.9 |
| repli_tendance_2r (test) | 2383 | 31.4 | 0.12 | 1.31 | 1299.3 | -36.6 |
| repli_tendance_vente (test) | 47 | 23.4 | -0.08 | 0.81 | -4.2 | -9.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1092 | 39.5 | 0.34 | 1.57 | 3352.0 | -37.2 |
| rsi2_repli | 4144 | 64.4 | 0.03 | 1.14 | 207.7 | -65.8 |
| cassure_20j | 2919 | 40.9 | 0.26 | 1.5 | 137911.5 | -50.7 |
| tendance_mm_vente | 60 | 20.0 | -0.35 | 0.55 | -19.7 | -18.8 |
| cassure_20j_vente | 162 | 17.9 | -0.45 | 0.39 | -52.1 | -51.6 |
| repli_tendance | 2247 | 31.9 | 0.12 | 1.29 | 1205.4 | -40.3 |
| repli_tendance_2r (test) | 2459 | 35.5 | 0.12 | 1.29 | 1415.9 | -39.4 |
| repli_tendance_vente (test) | 72 | 16.7 | -0.19 | 0.64 | -13.1 | -21.2 |

## Day trading en barrières IG (indices, cassure du plus haut ou du plus bas de la veille)

Un trade par jour au plus, clôture en fin de séance. Si le stop et l'objectif sont touchés le même jour, le stop est compté (hypothèse prudente).

| Filtre de la veille | Sens | Knock-out | Trades | Réussite | Espérance par trade | Profit factor | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tous | deux_sens | 0.5 ATR | 12080 | 33.6 % | -0.34 R | 0.42 | -4108.9 R |
| tous | deux_sens | 1.0 ATR | 12080 | 43.8 % | -0.062 R | 0.73 | -745.1 R |
| tous | tendance | 0.5 ATR | 6947 | 33.4 % | -0.344 R | 0.41 | -2393.1 R |
| tous | tendance | 1.0 ATR | 6947 | 42.9 % | -0.083 R | 0.67 | -573.4 R |
| nr4 ⬅ | deux_sens | 0.5 ATR | 3577 | 35.7 % | -0.276 R | 0.48 | -986.1 R |
| nr4 | deux_sens | 1.0 ATR | 3577 | 43.9 % | -0.039 R | 0.81 | -140.9 R |
| nr4 | tendance | 0.5 ATR | 2023 | 35.3 % | -0.303 R | 0.45 | -612.9 R |
| nr4 | tendance | 1.0 ATR | 2023 | 43.0 % | -0.071 R | 0.69 | -143.2 R |
| inside | deux_sens | 0.5 ATR | 1526 | 33.6 % | -0.343 R | 0.41 | -523.3 R |
| inside | deux_sens | 1.0 ATR | 1526 | 43.3 % | -0.076 R | 0.68 | -116.2 R |
| inside | tendance | 0.5 ATR | 843 | 31.0 % | -0.425 R | 0.32 | -357.9 R |
| inside | tendance | 1.0 ATR | 843 | 40.8 % | -0.138 R | 0.5 | -116.6 R |

Par indice (réglage actuel ⬅) :

| Indice | Trades | Espérance par trade | Total |
| --- | --- | --- | --- |
| S&P 500 | 623 | -0.242 R | -150.7 R |
| Nasdaq 100 | 602 | -0.264 R | -159.2 R |
| DAX 40 | 582 | -0.302 R | -175.6 R |
| Nikkei 225 | 604 | -0.155 R | -93.5 R |
| FTSE 100 | 565 | -0.356 R | -201.0 R |
| CAC 40 | 601 | -0.343 R | -206.2 R |

## Loi des 20/80 par actif (stratégies envoyées, avec protections)

**25 actifs sur 56 (45 %) font 80 % des gains.**

Stabilité : les 11 meilleurs actifs de la 1re moitié (2021) font +0.15 R par trade dans la 2e moitié, contre +0.13 R pour les autres.

| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Caterpillar | 93 | +53.4 R | 5 % | +21.8 R | +31.5 R |
| 2 | Apple | 113 | +53.3 R | 9 % | +43.1 R | +10.3 R |
| 3 | AMD | 103 | +53.1 R | 14 % | +27.7 R | +25.3 R |
| 4 | Costco | 116 | +50.2 R | 18 % | +45.8 R | +4.3 R |
| 5 | Nasdaq 100 | 140 | +48.6 R | 23 % | +25.2 R | +23.4 R |
| 6 | Alphabet | 119 | +48.1 R | 27 % | +28.3 R | +19.7 R |
| 7 | S&P 500 | 141 | +45.4 R | 31 % | +27.9 R | +17.6 R |
| 8 | Nvidia | 132 | +45.1 R | 35 % | +20.9 R | +24.2 R |
| 9 | Eli Lilly | 96 | +42.5 R | 38 % | +23.7 R | +18.8 R |
| 10 | Cisco | 104 | +37.5 R | 42 % | +13.2 R | +24.4 R |
| 11 | Tesla | 93 | +36.3 R | 45 % | +31.5 R | +4.8 R |
| 12 | Home Depot | 88 | +35.6 R | 48 % | +33.1 R | +2.5 R |
| 13 | Morgan Stanley | 101 | +33.1 R | 51 % | +17.3 R | +15.8 R |
| 14 | Goldman Sachs | 104 | +32.6 R | 54 % | +7.8 R | +24.8 R |
| 15 | Mastercard | 104 | +31.6 R | 57 % | +22.1 R | +9.5 R |
| 16 | Microsoft | 130 | +31.2 R | 59 % | +32.3 R | -1.1 R |
| 17 | Walmart | 111 | +31.1 R | 62 % | +17.5 R | +13.6 R |
| 18 | JPMorgan | 103 | +31.1 R | 65 % | +9.8 R | +21.3 R |
| 19 | Berkshire Hathaway | 99 | +31.0 R | 67 % | +12.2 R | +18.8 R |
| 20 | Abbott | 114 | +28.5 R | 70 % | +20.9 R | +7.7 R |
| 21 | AbbVie | 103 | +26.4 R | 72 % | +15.3 R | +11.1 R |
| 22 | Amgen | 96 | +24.3 R | 74 % | +14.6 R | +9.7 R |
| 23 | Adobe | 93 | +23.7 R | 76 % | +31.3 R | -7.6 R |
| 24 | GE Aerospace | 83 | +23.5 R | 78 % | -3.1 R | +26.6 R |
| 25 | Salesforce | 97 | +22.5 R | 80 % | +10.3 R | +12.2 R |
| 26 | McDonald's | 92 | +20.2 R | 82 % | +23.6 R | -3.4 R |
| 27 | Wells Fargo | 86 | +15.3 R | 84 % | +11.4 R | +4.0 R |
| 28 | IBM | 84 | +14.9 R | 85 % | -4.7 R | +19.6 R |
| 29 | Bank of America | 98 | +14.2 R | 86 % | +5.8 R | +8.4 R |
| 30 | Netflix | 101 | +13.9 R | 87 % | +6.6 R | +7.3 R |
| 31 | Visa | 102 | +13.8 R | 89 % | +11.4 R | +2.3 R |
| 32 | PepsiCo | 89 | +13.2 R | 90 % | +15.5 R | -2.3 R |
| 33 | Philip Morris | 80 | +12.6 R | 91 % | +8.2 R | +4.4 R |
| 34 | Nikkei 225 | 142 | +12.1 R | 92 % | +8.8 R | +3.3 R |
| 35 | Coca-Cola | 101 | +12.0 R | 93 % | +8.5 R | +3.5 R |
| 36 | Broadcom | 135 | +11.5 R | 94 % | -6.9 R | +18.4 R |
| 37 | Intel | 84 | +11.4 R | 95 % | -4.5 R | +16.0 R |
| 38 | Intuit | 108 | +11.0 R | 96 % | +26.5 R | -15.6 R |
| 39 | Uber | 68 | +10.9 R | 97 % | +2.2 R | +8.7 R |
| 40 | Qualcomm | 95 | +10.3 R | 98 % | +9.7 R | +0.6 R |
| 41 | ServiceNow | 116 | +8.7 R | 98 % | +7.2 R | +1.5 R |
| 42 | Thermo Fisher | 110 | +8.4 R | 99 % | +22.3 R | -14.0 R |
| 43 | Exxon Mobil | 93 | +4.6 R | 100 % | +5.9 R | -1.3 R |
| 44 | Disney | 66 | +4.2 R | 100 % | -2.3 R | +6.5 R |
| 45 | Merck | 94 | +0.1 R | 100 % | -5.2 R | +5.3 R |
| 46 | Procter & Gamble | 93 | -1.4 R | 100 % | +6.5 R | -7.9 R |
| 47 | Johnson & Johnson | 103 | -2.2 R | 100 % | -4.6 R | +2.4 R |
| 48 | UnitedHealth | 95 | -2.4 R | 100 % | -2.4 R | -0.0 R |
| 49 | Amazon | 115 | -4.0 R | 100 % | +2.8 R | -6.8 R |
| 50 | Meta | 109 | -5.8 R | 100 % | -15.8 R | +10.1 R |
| 51 | Chevron | 95 | -8.2 R | 100 % | -1.7 R | -6.5 R |
| 52 | Oracle | 105 | -10.9 R | 100 % | -13.0 R | +2.1 R |
| 53 | DAX 40 | 144 | -19.5 R | 100 % | -6.1 R | -13.3 R |
| 54 | Texas Instruments | 134 | -22.4 R | 100 % | -9.5 R | -12.9 R |
| 55 | CAC 40 | 132 | -26.7 R | 100 % | -1.7 R | -25.0 R |
| 56 | FTSE 100 | 140 | -35.3 R | 100 % | -22.9 R | -12.3 R |

Résultats passés : aucune garantie pour l'avenir.
