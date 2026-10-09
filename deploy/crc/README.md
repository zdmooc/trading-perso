# Trading-perso sur CRC

Deux choses tournent sur CRC (allumé 24h/24), dans le projet `trading-perso` :

1. **La page web du marché** (`rapport-horaire.yaml`) : entrées et sorties du plan, graphiques, commentaire écrit
   par ton modèle local Ollama. Aucune clé nécessaire.
2. **Les déclencheurs** (`declencheurs.yaml`) : ils demandent à GitHub de lancer les workflows à l'heure exacte
   (plan 8h45, point 14h15, bilan 17h45, relevés IG, scan du soir), car GitHub a souvent des heures de retard.

Aucun ordre de bourse nulle part. Les clés ne sont jamais écrites dans un fichier : tu les tapes avec `read -s`.

## Page web du marché (sans aucune clé)

```bash
cd /c/workspaces/trading-perso && git pull
oc project trading-perso
oc delete secret rapport-horaire --ignore-not-found     # pas besoin de clés
oc apply -f deploy/crc/rapport-horaire.yaml
oc start-build rapport-horaire --follow                  # construit l'image depuis GitHub (quelques minutes)
oc rollout status deployment/rapport-horaire
```

Ouvre ensuite **https://marche-trading-perso.apps-crc.testing** dans ton navigateur. La page se recalcule
toutes les 15 minutes et se recharge seule toutes les 5 minutes.

En haut, « Que faire maintenant » : pour chaque indice, ATTENDRE (avec le niveau d'entrée), EN POSITION
(avec stop et objectif) ou TERMINÉ. Puis les graphiques. Le commentaire IA apparaît si Ollama répond.

Journal : `oc logs deployment/rapport-horaire`. Après une mise à jour du dépôt : `oc start-build rapport-horaire --follow`.

Facultatif : cours IG au lieu de Yahoo, en créant le secret `rapport-horaire` (IG_API_KEY, IG_USERNAME, IG_PASSWORD)
puis `oc rollout restart deployment/rapport-horaire`.

## 3. Déclencheurs (facultatif)

1. Sur GitHub : Settings › Developer settings › Fine-grained tokens › Generate new token.
   Dépôt : **zdmooc/trading-perso uniquement**. Permission : **Actions : Read and write**. Rien d'autre.
2. Dans Git Bash :

```bash
read -s GH_TOKEN
oc -n trading-perso create secret generic github-dispatch --from-literal=token="$GH_TOKEN"; unset GH_TOKEN
oc apply -f deploy/crc/declencheurs.yaml
oc -n trading-perso create job test-plan --from=cronjob/point-14h15 && oc -n trading-perso logs -f job/test-plan
```

## Vérifier, arrêter

```bash
oc -n trading-perso get cronjobs
oc -n trading-perso scale deployment/rapport-horaire --replicas=0   # arrêter la page
```

