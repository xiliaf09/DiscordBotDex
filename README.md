# Discord Bot for Base Blockchain Token Updates

Un bot Discord qui surveille les nouveaux tokens sur la blockchain Base et les mentions de cryptomonnaies dans les posts de Trump sur Truth Social.

## Fonctionnalités

- Surveillance des nouveaux tokens sur Base et Solana
- Détection des mentions de cryptomonnaies dans les posts de Trump
- Commandes pour activer/désactiver le monitoring par chaîne
- Surveillance des nouveaux tokens Clanker
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
   CHANNEL_ID=id_du_canal
   BASESCAN_API_KEY=votre_cle_api_basescan
   ```
4. Lancez le bot :
   ```bash
   python bot.py
   ```

## Configuration

Le bot utilise les variables d'environnement suivantes :
- `DISCORD_TOKEN` : Le token de votre bot Discord
- `CHANNEL_ID` : L'ID du canal où les notifications seront envoyées
- `BASESCAN_API_KEY` : Votre clé API Basescan pour accéder aux données de transactions

## Dépendances

- discord.py
- requests
- python-dotenv
- httpx
- feedparser
- web3

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
