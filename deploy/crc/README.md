# Déclencheurs CRC

GitHub lance ses tâches planifiées avec parfois des heures de retard. Ces CronJobs, sur CRC (allumé 24h/24),
demandent à GitHub de lancer les workflows à l'heure exacte de Paris. Ils n'ont accès qu'au jeton GitHub.

## Installation (une fois)

1. Sur GitHub : Settings › Developer settings › Fine-grained tokens › Generate new token.
   Dépôt : **zdmooc/trading-perso uniquement**. Permission : **Actions : Read and write**. Rien d'autre.
2. Dans Git Bash :

```bash
oc new-project trading-perso
read -s GH_TOKEN   # colle le jeton puis Entrée (rien ne s'affiche)
oc -n trading-perso create secret generic github-dispatch --from-literal=token="$GH_TOKEN"; unset GH_TOKEN
oc apply -f deploy/crc/declencheurs.yaml
```

## Test

```bash
oc -n trading-perso create job test-ig --from=cronjob/ig-12h
oc -n trading-perso logs job/test-ig    # doit afficher « ig.yml lancé »
oc -n trading-perso get cronjobs
```
