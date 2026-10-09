# Trading-perso sur CRC

Deux choses tournent sur CRC (allumé 24h/24), dans le projet `trading-perso` :

1. **Le rapport horaire avec commentaire IA** (`rapport-horaire.yaml`) : chaque heure de 9h05 à 22h05, cours IG démo
   en lecture seule, graphiques, commentaire écrit par ton modèle local Ollama, envoi Telegram sans sonnerie.
2. **Les déclencheurs** (`declencheurs.yaml`) : ils demandent à GitHub de lancer les workflows à l'heure exacte
   (plan 8h45, point 14h15, bilan 17h45, relevés IG, scan du soir), car GitHub a souvent des heures de retard.

Aucun ordre de bourse nulle part. Les clés ne sont jamais écrites dans un fichier : tu les tapes avec `read -s`.

## 0. Vérifier qu'Ollama répond depuis CRC

Ollama doit écouter sur l'adresse VirtualBox de Windows (variable Windows `OLLAMA_HOST=192.168.56.1:11434`).

```bash
MSYS_NO_PATHCONV=1 oc debug node/crc -- chroot /host curl -s http://192.168.56.1:11434/api/tags
```

La réponse doit lister `qwen2.5:3b`. Sinon : relancer Ollama après avoir posé `OLLAMA_HOST`, et autoriser le port
11434 dans le pare-feu Windows pour le réseau VirtualBox.

## 1. Projet et clés (une fois)

```bash
oc new-project trading-perso 2>/dev/null || oc project trading-perso
read -s IG_API_KEY; read -s IG_USERNAME; read -s IG_PASSWORD; read -s TELEGRAM_TOKEN; read -s TELEGRAM_CHAT_ID
oc -n trading-perso create secret generic rapport-horaire \
  --from-literal=IG_API_KEY="$IG_API_KEY" --from-literal=IG_USERNAME="$IG_USERNAME" \
  --from-literal=IG_PASSWORD="$IG_PASSWORD" --from-literal=TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
  --from-literal=TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
unset IG_API_KEY IG_USERNAME IG_PASSWORD TELEGRAM_TOKEN TELEGRAM_CHAT_ID
```

(`read -s` : colle la valeur puis Entrée, rien ne s'affiche. Une valeur par `read`.)

## 2. Rapport horaire

```bash
oc apply -f deploy/crc/rapport-horaire.yaml
oc -n trading-perso start-build rapport-horaire --follow      # construit l'image depuis GitHub (quelques minutes)
oc -n trading-perso create job test-rapport --from=cronjob/rapport-horaire
oc -n trading-perso logs -f job/test-rapport
```

Le journal doit finir par `Rapport écrit`, et tu reçois le rapport sur Telegram avec le commentaire.
Si le journal affiche `IA indisponible`, le rapport part quand même, sans commentaire : revoir l'étape 0.
Si `Commentaire IA retiré`, le modèle a cité un nombre absent des données : c'est le garde-fou qui marche.

Après une mise à jour du dépôt : `oc -n trading-perso start-build rapport-horaire --follow`.

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
oc -n trading-perso patch cronjob rapport-horaire -p '{"spec":{"suspend":true}}'   # pause
oc -n trading-perso delete job test-rapport test-plan --ignore-not-found
```

Quand le rapport tourne sur CRC, dis-le à Claude : il coupera l'envoi horaire de GitHub pour éviter les doublons.
