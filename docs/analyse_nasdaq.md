# Nasdaq 100 : analyse du 06/10/2026

Cours de référence : **31 076** (clôture du 05/10/2026). Simulation et statistiques, pas un conseil.
Rapports bruts : `reports/divergence_NDX.md`, `reports/fin_annee_NDX.md`, `reports/replis_NDX.md`.

## 1. Situation

- +5 870 pts depuis janvier (+23 %), au plus haut de l'année.
- +1 560 pts au-dessus de la moyenne 50 jours (29 517), +3 570 pts au-dessus de la 200 jours (27 508).
- RSI 14 daily 68. Une journée bouge en moyenne de 380 pts (ATR 14).
- Freins : taux US 10 ans à 5,3 % en forte hausse, hausse déjà importante.

## 2. Divergences RSI 14

| Unité | Sommet précédent | Dernier sommet | Divergence baissière |
| --- | --- | --- | --- |
| Mensuel | mai : 30 333 (RSI 78) | oct. : 31 076 (RSI 73), +743 pts | oui, à confirmer à la clôture d'octobre |
| Hebdo | 10/08 : 30 046 (RSI 62) | 05/10 : 31 076 (RSI 66) | non |
| Daily | 22/09 : 30 732 (RSI 68) | 05/10 : 31 076 (RSI 68) | non (RSI à plat) |

Un vrai signal de vente : divergence aussi en daily, puis cassure sous le creux récent.

## 3. Fin d'année (41 ans d'historique, du 6 octobre au 31 décembre)

32 années sur 41 en hausse, médiane +5,5 %.

| Scénario | Niveau au 31/12 | Points |
| --- | --- | --- |
| Mauvais (1 an sur 10) | 27 350 | −3 730 |
| Prudent (1 an sur 4) | 31 265 | +190 |
| Médian | 32 780 | +1 700 |
| Bon (1 an sur 4) | 34 800 | +3 720 |
| Très bon (1 an sur 10) | 38 000 | +6 920 |

Estimation retenue : **31 000 à 33 000** (taux et divergence mensuelle tirent vers le bas de la médiane).
Seuil d'alerte : sous la moyenne 50 jours (≈ 29 500).

## 4. Zones d'achat sur repli

Sur 10 ans, un repli en tendance haussière fait en médiane −1 150 pts ; 3 sur 4 restent sous −2 330 pts.
Les zones sont dans `config.toml` (`[zones."^NDX"]`) : les modifier là, le graphe suit.

| Zone | Achat | Stop | Objectif 3R | Raison |
| --- | --- | --- | --- | --- |
| 1 | 30 700 | 30 200 | 32 200 | anciens sommets de juin et septembre |
| 2 (meilleure) | 29 950 | 29 400 | 31 600 | moyenne 20 j + taille d'un repli moyen |
| 3 | 29 500 | 28 950 | 31 150 | moyennes 50 et 100 jours |
| 4 | 28 750 | 28 100 | 30 700 | plus bas du mois, limite de 3 replis sur 4 |

Sous **28 100** : tendance cassée, plus d'achat.

Règles : attendre une bougie daily qui clôture en hausse dans la zone (pas d'achat « au toucher »),
répartir la mise sur plusieurs zones, stop d'au moins 400 pts (le bruit d'une journée).
Contrat IG mini à 1 €/point, taille 0,5 : un stop de 550 pts = 275 € de risque.

## 5. Suivi automatique chaque soir

Le scan du soir (`scan.yml`, lancé à 23h par CRC) exécute `scripts/graphe.py ^NDX` :

- `reports/graphe_NDX.png` : dernier graphe ; `reports/graphes/NDX_AAAA-MM-JJ.png` : archive datée (versionnée dans Git) ;
- `reports/zones_NDX.csv` : état de chaque zone chaque soir ;
- message Telegram avec le graphe.

États : **en attente** (pas atteinte), **touchée** (plus bas dans la zone), **confirmée** (touchée et bougie haussière :
le signal d'achat), **cassée** (clôture sous le stop).

## 6. Outils à la demande (sans Claude)

GitHub › Actions › **analyse-europe** › Run workflow, champ `outil` :
`divergence`, `fin_annee`, `replis` ou `graphe`, et `symbole` : `^NDX`, `^GSPC`, `^GDAXI`, `^FCHI`.
