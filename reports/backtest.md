# Backtest sur 10y (57 actifs, frais 5 bps, risque 1% par trade)

## Résultat réaliste du portefeuille (stratégies actives, 4 positions au maximum)

**+8.5 % par an** (+121.8 % au total), pire baisse **-23.8 %**, plus longue période sous un ancien sommet : 38.5 mois.

| Trades | Réussite | Gain moyen | Perte moyenne | Espérance par trade | Profit factor |
| --- | --- | --- | --- | --- | --- |
| 551 | 29.9 % | +2.03 R | -0.63 R | +0.16 R | 1.37 |

Par stratégie : cassure_20j 210 trades (+32.2 R), cassure_20j_vente 69 trades (-4.0 R), repli_tendance 193 trades (+19.2 R), tendance_mm 70 trades (+43.9 R), tendance_mm_vente 9 trades (-0.5 R).

### Comparaison avec « acheter et garder » (02/2017 à 10/2026)

| Méthode | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| **Ce système** (4 positions, risque 1% par trade) | +8.5 % | +121.8 % | -23.8 % | 38.5 mois |
| Garder le S&P 500 (ETF SPY, dividendes inclus) | +15.1 % | +290.7 % | -33.7 % | 23.2 mois |
| Garder le Nasdaq 100 (ETF QQQ, dividendes inclus) | +20.2 % | +499.2 % | -35.1 % | 23.5 mois |
| Garder Apple, Microsoft, Alphabet, Amazon, Meta et Nvidia (parts égales) | +35.6 % | +1828.2 % | -46.6 % | 18.1 mois |

### Spéculation : rotation sur les actions leaders (actions réelles, parts égales)

| Variante | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| Avec filtre de marché | +13.8 % | +242.3 % | -29.8 % | 22.3 mois |
| Sans filtre de marché | +19.4 % | +437.7 % | -39.4 % | 18.4 mois |

⚠️ Biais : la liste contient les grandes actions d'aujourd'hui, donc des gagnantes connues après coup. Le résultat réel sera plus faible.


## Solidité des réglages

Si un petit changement de réglage fait s'effondrer le résultat, la stratégie est trop ajustée au passé.

| Variante | Trades | Espérance par trade | Rendement par an | Pire baisse |
| --- | --- | --- | --- | --- |
| Réglage actuel | 551 | +0.16 R | +8.5 % | -23.8 % |
| Cassure sur 15 jours | 562 | +0.14 R | +7.1 % | -26.8 % |
| Cassure sur 25 jours | 560 | +0.16 R | +8.7 % | -28.4 % |
| Moyenne longue 150 jours | 568 | +0.16 R | +8.7 % | -24.3 % |
| Moyenne longue 250 jours | 561 | +0.24 R | +13.3 % | -21.6 % |
| Stop à 1,5 ATR | 711 | +0.13 R | +8.3 % | -29.8 % |
| Stop à 2,5 ATR | 452 | +0.19 R | +8.1 % | -15.2 % |
| Sans stop au prix d'entrée | 525 | +0.11 R | +5.0 % | -21.1 % |
| Sans filtre de marché | 621 | +0.23 R | +13.8 % | -26.4 % |

# Détail par stratégie (trades indépendants)

Ventes à découvert : indices uniquement. Ici, chaque trade est compté sans limite de positions simultanées : les rendements sont donc gonflés. Seuls le gain moyen (R) et le profit factor se comparent.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 892 | 28.8 | 0.26 | 1.56 | 829.0 | -31.6 |
| rsi2_repli | 3655 | 63.9 | 0.02 | 1.11 | 122.3 | -65.1 |
| cassure_20j | 2654 | 32.0 | 0.19 | 1.39 | 10354.6 | -49.8 |
| tendance_mm_vente | 34 | 11.8 | -0.36 | 0.39 | -11.6 | -10.6 |
| cassure_20j_vente | 106 | 19.8 | -0.17 | 0.68 | -17.6 | -21.6 |
| repli_tendance | 2199 | 27.2 | 0.14 | 1.39 | 1908.8 | -30.7 |
| repli_tendance_2r (test) | 2388 | 31.4 | 0.12 | 1.32 | 1364.4 | -36.6 |
| repli_tendance_vente (test) | 47 | 23.4 | -0.08 | 0.81 | -4.2 | -9.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1089 | 39.1 | 0.33 | 1.55 | 2954.6 | -37.2 |
| rsi2_repli | 4128 | 64.3 | 0.03 | 1.13 | 186.7 | -65.9 |
| cassure_20j | 2925 | 41.0 | 0.26 | 1.5 | 143835.5 | -50.3 |
| tendance_mm_vente | 61 | 19.7 | -0.37 | 0.53 | -20.8 | -20.0 |
| cassure_20j_vente | 166 | 18.7 | -0.43 | 0.41 | -51.9 | -52.3 |
| repli_tendance | 2244 | 31.9 | 0.13 | 1.3 | 1266.0 | -40.3 |
| repli_tendance_2r (test) | 2459 | 35.6 | 0.12 | 1.29 | 1493.1 | -39.4 |
| repli_tendance_vente (test) | 72 | 16.7 | -0.19 | 0.64 | -13.1 | -21.2 |

## Day trading en barrières IG (indices, cassure du plus haut ou du plus bas de la veille)

Un trade par jour au plus, clôture en fin de séance. Si le stop et l'objectif sont touchés le même jour, le stop est compté (hypothèse prudente).

| Filtre de la veille | Sens | Knock-out | Trades | Réussite | Espérance par trade | Profit factor | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tous | deux_sens | 0.5 ATR | 12080 | 33.5 % | -0.34 R | 0.42 | -4105.8 R |
| tous | deux_sens | 1.0 ATR | 12080 | 43.8 % | -0.062 R | 0.73 | -743.0 R |
| tous | tendance | 0.5 ATR | 6935 | 33.4 % | -0.342 R | 0.41 | -2375.0 R |
| tous | tendance | 1.0 ATR | 6935 | 42.9 % | -0.081 R | 0.67 | -564.1 R |
| nr4 ⬅ | deux_sens | 0.5 ATR | 3574 | 35.7 % | -0.275 R | 0.48 | -981.8 R |
| nr4 | deux_sens | 1.0 ATR | 3574 | 43.8 % | -0.039 R | 0.81 | -140.6 R |
| nr4 | tendance | 0.5 ATR | 2017 | 35.4 % | -0.299 R | 0.45 | -603.1 R |
| nr4 | tendance | 1.0 ATR | 2017 | 43.0 % | -0.068 R | 0.7 | -138.1 R |
| inside | deux_sens | 0.5 ATR | 1528 | 33.6 % | -0.343 R | 0.41 | -523.8 R |
| inside | deux_sens | 1.0 ATR | 1528 | 43.2 % | -0.077 R | 0.68 | -117.4 R |
| inside | tendance | 0.5 ATR | 839 | 31.0 % | -0.423 R | 0.33 | -355.1 R |
| inside | tendance | 1.0 ATR | 839 | 40.9 % | -0.138 R | 0.5 | -115.9 R |

Par indice (réglage actuel ⬅) :

| Indice | Trades | Espérance par trade | Total |
| --- | --- | --- | --- |
| S&P 500 | 623 | -0.247 R | -154.0 R |
| Nasdaq 100 | 600 | -0.27 R | -162.2 R |
| DAX 40 | 581 | -0.299 R | -173.7 R |
| Nikkei 225 | 604 | -0.146 R | -88.2 R |
| FTSE 100 | 565 | -0.351 R | -198.3 R |
| CAC 40 | 601 | -0.342 R | -205.5 R |

## Loi des 20/80 par actif (stratégies envoyées, avec protections)

**26 actifs sur 57 (46 %) font 80 % des gains.**

Stabilité : les 11 meilleurs actifs de la 1re moitié (2021) font +0.14 R par trade dans la 2e moitié, contre +0.12 R pour les autres.

| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AMD | 102 | +57.1 R | 5 % | +29.8 R | +27.3 R |
| 2 | Caterpillar | 93 | +53.4 R | 10 % | +21.8 R | +31.5 R |
| 3 | Apple | 114 | +51.1 R | 14 % | +44.0 R | +7.1 R |
| 4 | Costco | 116 | +50.2 R | 18 % | +45.8 R | +4.3 R |
| 5 | Nasdaq 100 | 142 | +48.9 R | 23 % | +26.2 R | +22.7 R |
| 6 | Alphabet | 121 | +46.8 R | 27 % | +28.3 R | +18.4 R |
| 7 | Nvidia | 133 | +46.3 R | 31 % | +23.5 R | +22.8 R |
| 8 | S&P 500 | 143 | +44.1 R | 34 % | +27.9 R | +16.3 R |
| 9 | Eli Lilly | 96 | +42.5 R | 38 % | +23.7 R | +18.8 R |
| 10 | Cisco | 103 | +38.6 R | 41 % | +14.2 R | +24.4 R |
| 11 | Tesla | 91 | +36.9 R | 45 % | +32.1 R | +4.8 R |
| 12 | Morgan Stanley | 98 | +36.3 R | 48 % | +19.5 R | +16.8 R |
| 13 | Home Depot | 88 | +35.6 R | 51 % | +33.1 R | +2.5 R |
| 14 | Goldman Sachs | 103 | +33.6 R | 54 % | +8.7 R | +24.9 R |
| 15 | Microsoft | 132 | +33.3 R | 57 % | +32.3 R | +1.0 R |
| 16 | Mastercard | 103 | +32.6 R | 59 % | +23.1 R | +9.5 R |
| 17 | JPMorgan | 102 | +31.1 R | 62 % | +9.8 R | +21.3 R |
| 18 | Berkshire Hathaway | 99 | +30.3 R | 65 % | +11.5 R | +18.8 R |
| 19 | Walmart | 110 | +29.0 R | 67 % | +16.4 R | +12.6 R |
| 20 | Abbott | 115 | +27.5 R | 70 % | +20.9 R | +6.7 R |
| 21 | AbbVie | 103 | +26.5 R | 72 % | +18.2 R | +8.3 R |
| 22 | Salesforce | 94 | +25.6 R | 74 % | +13.4 R | +12.2 R |
| 23 | Amgen | 96 | +23.8 R | 76 % | +14.1 R | +9.7 R |
| 24 | GE Aerospace | 84 | +23.1 R | 78 % | -3.5 R | +26.6 R |
| 25 | Adobe | 92 | +21.8 R | 80 % | +29.3 R | -7.6 R |
| 26 | McDonald's | 93 | +19.2 R | 82 % | +22.6 R | -3.4 R |
| 27 | Visa | 103 | +15.9 R | 83 % | +10.3 R | +5.6 R |
| 28 | Wells Fargo | 86 | +15.3 R | 84 % | +11.4 R | +4.0 R |
| 29 | IBM | 84 | +14.9 R | 86 % | -4.7 R | +19.6 R |
| 30 | Intel | 82 | +14.3 R | 87 % | -1.6 R | +16.0 R |
| 31 | PepsiCo | 87 | +14.0 R | 88 % | +16.2 R | -2.3 R |
| 32 | Netflix | 101 | +13.9 R | 89 % | +6.6 R | +7.3 R |
| 33 | Coca-Cola | 99 | +13.1 R | 90 % | +9.3 R | +3.8 R |
| 34 | Broadcom | 134 | +12.4 R | 91 % | -1.7 R | +14.1 R |
| 35 | Bank of America | 98 | +12.2 R | 93 % | +3.8 R | +8.4 R |
| 36 | Nikkei 225 | 142 | +11.0 R | 93 % | +9.7 R | +1.3 R |
| 37 | Intuit | 108 | +11.0 R | 94 % | +26.5 R | -15.6 R |
| 38 | Uber | 68 | +10.9 R | 95 % | +2.2 R | +8.7 R |
| 39 | ServiceNow | 114 | +10.8 R | 96 % | +9.2 R | +1.5 R |
| 40 | Qualcomm | 95 | +10.3 R | 97 % | +9.7 R | +0.6 R |
| 41 | Philip Morris | 83 | +9.8 R | 98 % | +8.2 R | +1.6 R |
| 42 | Thermo Fisher | 111 | +8.4 R | 99 % | +22.3 R | -14.0 R |
| 43 | Disney | 64 | +6.2 R | 99 % | -0.3 R | +6.5 R |
| 44 | Exxon Mobil | 93 | +4.6 R | 100 % | +5.9 R | -1.3 R |
| 45 | Procter & Gamble | 94 | +3.8 R | 100 % | +5.4 R | -1.7 R |
| 46 | SpaceX | 2 | -0.0 R | 100 % | +0.0 R | -0.0 R |
| 47 | Merck | 96 | -0.6 R | 100 % | -5.2 R | +4.6 R |
| 48 | UnitedHealth | 94 | -1.5 R | 100 % | -1.5 R | -0.0 R |
| 49 | Johnson & Johnson | 102 | -1.9 R | 100 % | -4.3 R | +2.4 R |
| 50 | Chevron | 94 | -3.4 R | 100 % | -0.2 R | -3.2 R |
| 51 | Amazon | 116 | -4.6 R | 100 % | +4.0 R | -8.7 R |
| 52 | Meta | 112 | -5.6 R | 100 % | -16.8 R | +11.2 R |
| 53 | Oracle | 106 | -12.9 R | 100 % | -14.0 R | +1.1 R |
| 54 | DAX 40 | 144 | -19.5 R | 100 % | -6.1 R | -13.3 R |
| 55 | CAC 40 | 132 | -26.7 R | 100 % | -1.7 R | -25.0 R |
| 56 | Texas Instruments | 136 | -27.1 R | 100 % | -12.1 R | -15.0 R |
| 57 | FTSE 100 | 139 | -34.2 R | 100 % | -21.9 R | -12.3 R |

Résultats passés : aucune garantie pour l'avenir.
