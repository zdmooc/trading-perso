# Backtest sur 10y (57 actifs, frais 5 bps, risque 1% par trade)

## Résultat réaliste du portefeuille (stratégies actives, 4 positions au maximum)

**+8.2 % par an** (+114.0 % au total), pire baisse **-23.8 %**, plus longue période sous un ancien sommet : 38.5 mois.

| Trades | Réussite | Gain moyen | Perte moyenne | Espérance par trade | Profit factor |
| --- | --- | --- | --- | --- | --- |
| 547 | 29.8 % | +2.01 R | -0.63 R | +0.16 R | 1.36 |

Par stratégie : cassure_20j 208 trades (+36.3 R), cassure_20j_vente 69 trades (-4.0 R), repli_tendance 192 trades (+18.4 R), tendance_mm 69 trades (+36.5 R), tendance_mm_vente 9 trades (-0.5 R).

### Comparaison avec « acheter et garder » (02/2017 à 10/2026)

| Méthode | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| **Ce système** (4 positions, risque 1% par trade) | +8.2 % | +114.0 % | -23.8 % | 38.5 mois |
| Garder le S&P 500 (ETF SPY, dividendes inclus) | +15.2 % | +294.7 % | -33.7 % | 23.2 mois |
| Garder le Nasdaq 100 (ETF QQQ, dividendes inclus) | +20.7 % | +519.3 % | -35.1 % | 23.5 mois |
| Garder Apple, Microsoft, Alphabet, Amazon, Meta et Nvidia (parts égales) | +36.1 % | +1883.2 % | -46.6 % | 18.1 mois |

### Spéculation : rotation sur les actions leaders (actions réelles, parts égales)

| Variante | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |
| --- | --- | --- | --- | --- |
| Avec filtre de marché | +13.2 % | +224.4 % | -29.7 % | 22.3 mois |
| Sans filtre de marché | +19.3 % | +434.9 % | -39.4 % | 18.4 mois |

⚠️ Biais : la liste contient les grandes actions d'aujourd'hui, donc des gagnantes connues après coup. Le résultat réel sera plus faible.


## Solidité des réglages

Si un petit changement de réglage fait s'effondrer le résultat, la stratégie est trop ajustée au passé.

| Variante | Trades | Espérance par trade | Rendement par an | Pire baisse |
| --- | --- | --- | --- | --- |
| Réglage actuel | 547 | +0.16 R | +8.2 % | -23.8 % |
| Cassure sur 15 jours | 564 | +0.13 R | +6.4 % | -26.8 % |
| Cassure sur 25 jours | 554 | +0.16 R | +8.3 % | -28.4 % |
| Moyenne longue 150 jours | 567 | +0.17 R | +9.0 % | -24.3 % |
| Moyenne longue 250 jours | 561 | +0.23 R | +12.8 % | -21.6 % |
| Stop à 1,5 ATR | 703 | +0.14 R | +9.2 % | -29.8 % |
| Stop à 2,5 ATR | 447 | +0.19 R | +8.3 % | -15.2 % |
| Sans stop au prix d'entrée | 522 | +0.09 R | +4.2 % | -21.1 % |
| Sans filtre de marché | 625 | +0.25 R | +15.2 % | -26.4 % |

# Détail par stratégie (trades indépendants)

Ventes à découvert : indices uniquement. Ici, chaque trade est compté sans limite de positions simultanées : les rendements sont donc gonflés. Seuls le gain moyen (R) et le profit factor se comparent.

## Avec protections

Filtre de marché S&P 500 / MM200 : oui. Stop ramené au prix d'entrée à +1.0 R : oui.

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 894 | 28.7 | 0.26 | 1.56 | 812.2 | -31.6 |
| rsi2_repli | 3657 | 64.0 | 0.02 | 1.12 | 124.7 | -65.2 |
| cassure_20j | 2656 | 31.9 | 0.19 | 1.39 | 9808.3 | -49.8 |
| tendance_mm_vente | 34 | 11.8 | -0.36 | 0.39 | -11.6 | -10.6 |
| cassure_20j_vente | 106 | 19.8 | -0.17 | 0.68 | -17.6 | -21.6 |
| repli_tendance | 2197 | 27.3 | 0.14 | 1.39 | 1905.9 | -30.7 |
| repli_tendance_2r (test) | 2384 | 31.4 | 0.12 | 1.32 | 1344.6 | -36.3 |
| repli_tendance_vente (test) | 47 | 23.4 | -0.08 | 0.81 | -4.2 | -9.6 |

## Sans protections (pour comparaison)

| stratégie | trades | reussite_pct | r_moyen | profit_factor | rendement_pct | drawdown_max_pct |
| --- | --- | --- | --- | --- | --- | --- |
| tendance_mm | 1092 | 39.2 | 0.33 | 1.56 | 3046.3 | -37.2 |
| rsi2_repli | 4132 | 64.4 | 0.03 | 1.13 | 190.8 | -65.9 |
| cassure_20j | 2919 | 41.1 | 0.26 | 1.51 | 144596.0 | -50.1 |
| tendance_mm_vente | 60 | 20.0 | -0.35 | 0.55 | -19.7 | -18.8 |
| cassure_20j_vente | 164 | 17.7 | -0.45 | 0.39 | -53.1 | -52.6 |
| repli_tendance | 2248 | 31.9 | 0.12 | 1.3 | 1241.4 | -40.3 |
| repli_tendance_2r (test) | 2461 | 35.5 | 0.12 | 1.29 | 1436.8 | -39.2 |
| repli_tendance_vente (test) | 72 | 16.7 | -0.19 | 0.64 | -13.1 | -21.2 |

## Day trading en barrières IG (indices, cassure du plus haut ou du plus bas de la veille)

Un trade par jour au plus, clôture en fin de séance. Si le stop et l'objectif sont touchés le même jour, le stop est compté (hypothèse prudente).

| Filtre de la veille | Sens | Knock-out | Trades | Réussite | Espérance par trade | Profit factor | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tous | deux_sens | 0.5 ATR | 12083 | 33.6 % | -0.34 R | 0.42 | -4108.9 R |
| tous | deux_sens | 1.0 ATR | 12083 | 43.8 % | -0.062 R | 0.73 | -750.0 R |
| tous | tendance | 0.5 ATR | 6940 | 33.5 % | -0.343 R | 0.41 | -2380.5 R |
| tous | tendance | 1.0 ATR | 6940 | 42.9 % | -0.082 R | 0.67 | -567.5 R |
| nr4 ⬅ | deux_sens | 0.5 ATR | 3576 | 35.7 % | -0.275 R | 0.48 | -982.1 R |
| nr4 | deux_sens | 1.0 ATR | 3576 | 43.8 % | -0.039 R | 0.81 | -140.5 R |
| nr4 | tendance | 0.5 ATR | 2021 | 35.4 % | -0.301 R | 0.45 | -607.7 R |
| nr4 | tendance | 1.0 ATR | 2021 | 43.0 % | -0.069 R | 0.7 | -139.4 R |
| inside | deux_sens | 0.5 ATR | 1525 | 33.6 % | -0.342 R | 0.41 | -522.2 R |
| inside | deux_sens | 1.0 ATR | 1525 | 43.2 % | -0.076 R | 0.68 | -116.5 R |
| inside | tendance | 0.5 ATR | 842 | 31.0 % | -0.424 R | 0.33 | -357.2 R |
| inside | tendance | 1.0 ATR | 842 | 40.9 % | -0.138 R | 0.5 | -116.5 R |

Par indice (réglage actuel ⬅) :

| Indice | Trades | Espérance par trade | Total |
| --- | --- | --- | --- |
| S&P 500 | 623 | -0.241 R | -150.1 R |
| Nasdaq 100 | 601 | -0.269 R | -161.9 R |
| DAX 40 | 582 | -0.301 R | -175.1 R |
| Nikkei 225 | 604 | -0.152 R | -91.6 R |
| FTSE 100 | 565 | -0.351 R | -198.2 R |
| CAC 40 | 601 | -0.341 R | -205.2 R |

## Loi des 20/80 par actif (stratégies envoyées, avec protections)

**25 actifs sur 57 (44 %) font 80 % des gains.**

Stabilité : les 11 meilleurs actifs de la 1re moitié (2021) font +0.15 R par trade dans la 2e moitié, contre +0.13 R pour les autres.

| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AMD | 102 | +57.1 R | 5 % | +29.8 R | +27.3 R |
| 2 | Caterpillar | 93 | +53.4 R | 10 % | +21.8 R | +31.5 R |
| 3 | Apple | 114 | +52.9 R | 14 % | +45.8 R | +7.1 R |
| 4 | Costco | 116 | +50.2 R | 19 % | +45.8 R | +4.3 R |
| 5 | Nasdaq 100 | 141 | +49.5 R | 23 % | +26.2 R | +23.3 R |
| 6 | Alphabet | 119 | +48.1 R | 27 % | +28.3 R | +19.7 R |
| 7 | S&P 500 | 142 | +44.4 R | 31 % | +27.9 R | +16.5 R |
| 8 | Nvidia | 135 | +43.7 R | 35 % | +20.9 R | +22.8 R |
| 9 | Eli Lilly | 96 | +42.5 R | 38 % | +23.7 R | +18.8 R |
| 10 | Cisco | 104 | +37.7 R | 42 % | +13.3 R | +24.4 R |
| 11 | Tesla | 93 | +36.3 R | 45 % | +31.5 R | +4.8 R |
| 12 | Home Depot | 88 | +35.6 R | 48 % | +33.1 R | +2.5 R |
| 13 | Morgan Stanley | 99 | +35.3 R | 51 % | +18.5 R | +16.9 R |
| 14 | Microsoft | 131 | +34.3 R | 54 % | +32.3 R | +2.0 R |
| 15 | Goldman Sachs | 104 | +32.6 R | 57 % | +7.8 R | +24.8 R |
| 16 | Mastercard | 103 | +32.6 R | 59 % | +23.1 R | +9.5 R |
| 17 | JPMorgan | 103 | +30.1 R | 62 % | +8.8 R | +21.3 R |
| 18 | Berkshire Hathaway | 100 | +29.3 R | 65 % | +10.5 R | +18.8 R |
| 19 | Walmart | 111 | +29.0 R | 67 % | +15.3 R | +13.6 R |
| 20 | Abbott | 114 | +28.5 R | 70 % | +20.9 R | +7.7 R |
| 21 | AbbVie | 103 | +26.4 R | 72 % | +18.1 R | +8.3 R |
| 22 | Salesforce | 95 | +24.6 R | 74 % | +12.3 R | +12.2 R |
| 23 | Amgen | 96 | +23.8 R | 76 % | +14.1 R | +9.7 R |
| 24 | GE Aerospace | 83 | +23.5 R | 78 % | -3.1 R | +26.6 R |
| 25 | Adobe | 92 | +22.3 R | 80 % | +29.8 R | -7.6 R |
| 26 | McDonald's | 92 | +20.2 R | 82 % | +23.6 R | -3.4 R |
| 27 | Wells Fargo | 85 | +15.6 R | 83 % | +11.6 R | +4.0 R |
| 28 | IBM | 84 | +14.9 R | 84 % | -4.7 R | +19.6 R |
| 29 | Bank of America | 98 | +14.2 R | 86 % | +5.8 R | +8.4 R |
| 30 | Coca-Cola | 99 | +14.1 R | 87 % | +10.3 R | +3.8 R |
| 31 | PepsiCo | 88 | +13.9 R | 88 % | +16.1 R | -2.3 R |
| 32 | Netflix | 101 | +13.9 R | 89 % | +6.6 R | +7.3 R |
| 33 | Visa | 102 | +13.8 R | 90 % | +11.4 R | +2.4 R |
| 34 | Philip Morris | 80 | +12.6 R | 92 % | +8.2 R | +4.4 R |
| 35 | Intel | 84 | +12.3 R | 93 % | -3.6 R | +16.0 R |
| 36 | Qualcomm | 95 | +11.6 R | 94 % | +9.7 R | +1.9 R |
| 37 | Broadcom | 135 | +11.3 R | 95 % | -5.8 R | +17.2 R |
| 38 | Intuit | 108 | +11.0 R | 96 % | +26.5 R | -15.6 R |
| 39 | Uber | 68 | +10.9 R | 97 % | +2.2 R | +8.7 R |
| 40 | Nikkei 225 | 143 | +10.2 R | 97 % | +8.9 R | +1.3 R |
| 41 | ServiceNow | 115 | +9.7 R | 98 % | +8.2 R | +1.5 R |
| 42 | Thermo Fisher | 110 | +8.4 R | 99 % | +22.3 R | -14.0 R |
| 43 | Disney | 64 | +6.2 R | 100 % | -0.3 R | +6.5 R |
| 44 | Exxon Mobil | 93 | +4.6 R | 100 % | +5.9 R | -1.3 R |
| 45 | Procter & Gamble | 93 | +0.8 R | 100 % | +5.4 R | -4.6 R |
| 46 | Merck | 94 | +0.1 R | 100 % | -5.2 R | +5.3 R |
| 47 | SpaceX | 2 | -0.0 R | 100 % | +0.0 R | -0.0 R |
| 48 | Johnson & Johnson | 103 | -2.2 R | 100 % | -4.6 R | +2.4 R |
| 49 | UnitedHealth | 95 | -2.5 R | 100 % | -2.5 R | -0.0 R |
| 50 | Chevron | 95 | -4.5 R | 100 % | -1.2 R | -3.2 R |
| 51 | Amazon | 116 | -4.6 R | 100 % | +4.0 R | -8.7 R |
| 52 | Meta | 110 | -6.8 R | 100 % | -16.8 R | +10.0 R |
| 53 | Oracle | 106 | -12.4 R | 100 % | -13.5 R | +1.1 R |
| 54 | DAX 40 | 144 | -19.5 R | 100 % | -6.1 R | -13.3 R |
| 55 | CAC 40 | 132 | -26.7 R | 100 % | -1.7 R | -25.0 R |
| 56 | Texas Instruments | 136 | -27.1 R | 100 % | -12.1 R | -15.0 R |
| 57 | FTSE 100 | 140 | -35.3 R | 100 % | -22.9 R | -12.3 R |

Résultats passés : aucune garantie pour l'avenir.
