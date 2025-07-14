# Discord Bot for Base Blockchain Token Updates

Un bot Discord qui surveille les nouveaux tokens sur la blockchain Base et les mentions de cryptomonnaies dans les posts de Trump sur Truth Social.

## Fonctionnalités

- Surveillance des nouveaux tokens sur Base et Solana
- Détection des mentions de cryptomonnaies dans les posts de Trump
- Commandes pour activer/désactiver le monitoring par chaîne
- Surveillance des nouveaux tokens Clanker (on-chain)
- Surveillance des nouveaux tokens Clanker V4 (on-chain)
- Surveillance des nouveaux tokens Doppler (on-chain)
- Affichage des informations détaillées des tokens
- Tracking des transactions de wallets sur Base
- Système de snipe automatique basé sur FID
- Gestion des whitelist/blacklist de FIDs

## Commandes

### Commandes Générales
- `!test` - Envoie un message test pour vérifier que le bot fonctionne
- `!status` - Affiche le statut du monitoring pour chaque chaîne
- `!help` - Affiche la liste complète des commandes

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
- `!lastclankerv4` - Affiche le dernier token déployé sur Clanker V4

### Commandes Doppler
- `!doppleron` - Active le monitoring des nouveaux tokens Doppler
- `!doppleroff` - Désactive le monitoring des nouveaux tokens Doppler
- `!lastdoppler` - Affiche le dernier token déployé sur Doppler

### Commandes de Volume
- `!volume <contract>` - Affiche le volume du token sur 24h, 6h, 1h, 5min
- `!setvolume <usd>` - Définit le seuil global d'alerte volume (5min)

### Commandes de Gestion FID
- `!banfid <fid>` - Bannit un FID pour ne plus recevoir ses alertes
- `!unbanfid <fid>` - Débannit un FID
- `!listbanned` - Affiche la liste des FIDs bannis
- `!whitelist <fid>` - Ajoute un FID à la whitelist (alertes premium)
- `!removewhitelist <fid>` - Retire un FID de la whitelist
- `!checkwhitelist` - Affiche la liste des FIDs whitelistés
- `!fidcheck <contract>` - Vérifie le FID associé à un contrat Clanker
- `!spamcheck` - Liste les FIDs ayant déployé plus d'un token dans les dernières 24h

### Commandes d'Import/Export
- `!importbanlist` - Importe des listes de FIDs à bannir depuis des fichiers
- `!exportbanlist` - Exporte la liste des FIDs bannis
- `!importwhitelist` - Importe des listes de FIDs depuis des fichiers
- `!exportwhitelist` - Exporte la liste des FIDs whitelistés
- `!importfollowing <username> <limit>` - Importe les FIDs des comptes suivis par un utilisateur Warpcast

### Commandes de Snipe
- `!snipe <fid> <amount> <gas_fees>` - Configure un snipe pour un FID spécifique
- `!listsnipes` - Liste tous les snipes en attente
- `!cancelsnipe <fid>` - Annule un snipe en attente
- `!editsnipe <fid> <new_amount>` - Modifie le montant d'un snipe
- `!clearsnipes` - Supprime tous les snipes en attente
- `!buywebhook <contract> <amount> <gas_fees>` - Déclenche un achat via webhook
- `!buytg <contract> <amount>` - Envoie une commande d'achat au bot Telegram

### Commandes de Trading
- `!buy <token_address> <amount>` - Achete un token via Uniswap V3
- `!deployclanker <name> <symbol> <fid> <image> <devbuy_eth>` - Déploie un token Clanker

### Commandes de Test
- `!testvolumealert` - Simule une alerte de volume
- `!testtelegram` - Teste la connexion avec le bot Telegram

## Installation

### Déploiement Local
1. Clonez le repository
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Créez un fichier `.env` avec les variables suivantes :
   ```
   DISCORD_TOKEN=votre_token_discord
   CHANNEL_ID=id_du_canal
   QUICKNODE_WSS=votre_quicknode_wss
   BASESCAN_API_KEY=votre_cle_api_basescan
   ```
4. Lancez le bot :
   ```bash
   python bot.py
   ```

### Déploiement sur Railway (Recommandé)
1. Connectez votre compte Railway à GitHub
2. Créez un nouveau projet depuis ce dépôt
3. Ajoutez les variables d'environnement dans les paramètres du projet Railway :
   - `DISCORD_TOKEN` : Le token de votre bot Discord
   - `CHANNEL_ID` : L'ID du canal où les notifications seront envoyées
   - `QUICKNODE_WSS` : Votre endpoint WebSocket QuickNode pour la surveillance on-chain
   - `BASESCAN_API_KEY` : Votre clé API Basescan pour accéder aux données de transactions
4. Railway déploiera automatiquement le bot

## Configuration

Le bot utilise les variables d'environnement suivantes :
- `DISCORD_TOKEN` : Le token de votre bot Discord
- `CHANNEL_ID` : L'ID du canal où les notifications seront envoyées
- `QUICKNODE_WSS` : Votre endpoint WebSocket QuickNode pour la surveillance on-chain
- `BASESCAN_API_KEY` : Votre clé API Basescan pour accéder aux données de transactions

## Dépendances

- discord.py
- requests
- python-dotenv
- httpx
- feedparser
- web3
- aiohttp
- sqlite3

## Fonctionnalités Avancées

### Surveillance On-Chain
Le bot surveille en temps réel les déploiements de tokens sur :
- Clanker Factory (Base)
- Clanker Factory V4 (Base)
- Doppler Factory (Base)

### Système de Snipe
- Configuration de snipes basés sur FID
- Exécution automatique via webhook
- Intégration avec bot Telegram

### Gestion des FIDs
- Whitelist pour les alertes premium
- Blacklist pour filtrer les spammeurs
- Import/export de listes
- Vérification des FIDs associés aux contrats

### Monitoring de Volume
- Surveillance automatique du volume des tokens
- Alertes personnalisables
- Intégration avec Dexscreener

## Maintenance

- Les tokens vus sont stockés dans `seen_tokens.json`
- Les tokens Clanker vus sont stockés dans `seen_clanker_tokens.json`
- Les tokens Doppler vus sont stockés dans `seen_doppler_tokens.json`
- Les logs sont écrits dans `bot.log`
- Le bot garde en mémoire les 100 derniers posts de Trump vérifiés
- Les wallets suivis sont stockés dans `tracked_wallets.json`
- Les FIDs bannis sont stockés dans `banned_fids.json`
- Les FIDs whitelistés sont stockés dans `whitelisted_fids.json`

## Optimisations Railway

Le bot est optimisé pour fonctionner sur Railway avec :
- Gestion automatique des reconnexions WebSocket
- Délais adaptés pour réduire l'utilisation des ressources
- Gestion robuste des erreurs de connexion
- Surveillance de la santé des connexions

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.
