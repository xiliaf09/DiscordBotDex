# Discord Bot for Base Blockchain Token Updates

Un bot Discord qui surveille les nouveaux tokens sur la blockchain Base et les mentions de cryptomonnaies dans les posts de Trump sur Truth Social.

## Fonctionnalités

- Surveillance des nouveaux tokens sur Base et Solana
- Détection des mentions de cryptomonnaies dans les posts de Trump
- Commandes pour activer/désactiver le monitoring par chaîne
- Surveillance des nouveaux tokens Clanker
- **Alertes volume critiques avec notifications Pushover** (son d'alarme, bypass silencieux/DND)
- **Appels téléphoniques d'urgence Twilio** pour volumes > 50k USD
- Affichage des informations détaillées des tokens
- Tracking des transactions de wallets sur Base

## Commandes

### Commandes Générales
- `!test` - Envoie un message test pour vérifier que le bot fonctionne
- `!status` - Affiche le statut du monitoring pour chaque chaîne

### Commandes Base
- `!baseon` - Active le monitoring pour Base
- `!baseoff` - Désactive le monitoring pour Base

### Commandes Solana
- `!solanaon` - Active le monitoring pour Solana
- `!solanaoff` - Désactive le monitoring pour Solana

### Commandes Trump
- `!lasttrump` - Affiche le dernier post de Trump sur Truth Social

### Commandes Clanker
- `!clankeron` - Active le monitoring des nouveaux tokens Clanker
- `!clankeroff` - Désactive le monitoring des nouveaux tokens Clanker
- `!lastclanker` - Affiche le dernier token déployé sur Clanker
- `!setvolume <montant>` - Définit le seuil d'alerte volume (défaut: 15000 USD sur 24h)
- `!setemergencycall <montant>` - Définit le seuil d'appel d'urgence Twilio (défaut: 50000 USD)
- `!testpushover` - Teste la connexion Pushover (admin uniquement)
- `!testtwilio` - Teste la connexion Twilio avec un appel (admin uniquement)

### Commandes de Tracking de Wallet
- `!track <adresse_wallet>` - Active le suivi des transactions d'un wallet sur Base
- `!stoptrack <adresse_wallet>` - Désactive le suivi des transactions d'un wallet

## Installation

1. Clonez le repository
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Créez un fichier `.env` avec les variables suivantes :
   ```
   DISCORD_TOKEN=votre_token_discord
   DISCORD_CHANNEL_ID=id_du_canal
   ADMIN_ROLE_ID=id_du_role_admin
   BASE_RPC_URL=votre_url_rpc_base
   WALLET_PRIVATE_KEY=votre_cle_privee_wallet
   WALLET_ADDRESS=votre_adresse_wallet
   CLANKER_API_KEY=votre_cle_api_clanker
   CLANKER_API_SECRET=votre_secret_api_clanker
   QUICKNODE_WSS=votre_url_websocket_quicknode
   PUSHOVER_API_TOKEN=votre_token_api_pushover
   PUSHOVER_USER_KEY=votre_cle_utilisateur_pushover
   PUSHOVER_API_TOKEN_2=token_api_pushover_ami (optionnel)
   PUSHOVER_USER_KEY_2=cle_utilisateur_pushover_ami (optionnel)
   TWILIO_ACCOUNT_SID=votre_account_sid_twilio
   TWILIO_AUTH_TOKEN=votre_auth_token_twilio
   TWILIO_PHONE_NUMBER=+1234567890 (votre numéro Twilio)
   YOUR_PHONE_NUMBER=+1234567890 (votre numéro personnel)
   ```
4. Lancez le bot :
   ```bash
   python bot.py
   ```

## Configuration

Le bot utilise les variables d'environnement suivantes :
- `DISCORD_TOKEN` : Le token de votre bot Discord
- `DISCORD_CHANNEL_ID` : L'ID du canal où les notifications seront envoyées
- `ADMIN_ROLE_ID` : L'ID du rôle administrateur
- `BASE_RPC_URL` : URL RPC pour la blockchain Base
- `WALLET_PRIVATE_KEY` : Clé privée du wallet pour les transactions
- `WALLET_ADDRESS` : Adresse du wallet
- `CLANKER_API_KEY` : Clé API Clanker
- `CLANKER_API_SECRET` : Secret API Clanker
- `QUICKNODE_WSS` : URL WebSocket QuickNode pour l'écoute on-chain
- `PUSHOVER_API_TOKEN` : Token API Pushover (pour les alertes critiques - utilisateur 1)
- `PUSHOVER_USER_KEY` : Clé utilisateur Pushover (pour les alertes critiques - utilisateur 1)
- `PUSHOVER_API_TOKEN_2` : Token API Pushover (pour les alertes critiques - utilisateur 2, optionnel)
- `PUSHOVER_USER_KEY_2` : Clé utilisateur Pushover (pour les alertes critiques - utilisateur 2, optionnel)
- `TWILIO_ACCOUNT_SID` : Account SID Twilio (pour les appels d'urgence)
- `TWILIO_AUTH_TOKEN` : Auth Token Twilio (pour les appels d'urgence)
- `TWILIO_PHONE_NUMBER` : Numéro de téléphone Twilio (pour les appels d'urgence)
- `YOUR_PHONE_NUMBER` : Votre numéro de téléphone personnel (pour recevoir les appels)

### Configuration Pushover (Alertes Critiques)

Pour recevoir des notifications critiques sur iPhone avec son d'alarme :

1. Créez un compte sur [pushover.net](https://pushover.net/)
2. Installez l'app Pushover sur votre iPhone
3. Obtenez votre `PUSHOVER_USER_KEY` dans l'app
4. Créez une application sur pushover.net pour obtenir votre `PUSHOVER_API_TOKEN`
5. Ajoutez ces clés dans votre fichier `.env`

Les alertes volume utiliseront :
- **Priorité haute** (urgent, bypass silencieux/DND)
- **Son de sirène** pour attirer l'attention
- **Notification unique** (pas de répétition)
- **Envoi multiple** : Si vous configurez un deuxième utilisateur, les alertes seront envoyées aux deux
- **Appel téléphonique** : Pour les volumes > 50k USD, un appel vocal sera effectué

### Configuration Twilio (Appels d'Urgence)

Pour recevoir des appels téléphoniques automatiques sur les gros volumes :

1. Créez un compte sur [twilio.com](https://twilio.com)
2. Achetez un numéro de téléphone Twilio (recommandé : US, ~$1-2/mois)
3. Obtenez votre Account SID et Auth Token dans le dashboard
4. Ajoutez ces clés dans vos variables d'environnement

**Seuil d'appel :** 50 000 USD (configurable avec `!setemergencycall <montant>`)

## Dépendances

- discord.py
- requests
- python-dotenv
- httpx
- feedparser
- web3
- twilio (pour les appels d'urgence)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## Déploiement sur Railway

1. Connectez votre compte Railway à GitHub
2. Créez un nouveau projet depuis ce dépôt
3. Ajoutez les variables d'environnement dans les paramètres du projet
4. Railway déploiera automatiquement le bot

## Maintenance

- Les tokens vus sont stockés dans `seen_tokens.json`
- Les logs sont écrits dans `bot.log`
- Le bot garde en mémoire les 100 derniers posts de Trump vérifiés
- Les wallets suivis sont stockés dans `tracked_wallets.json`
