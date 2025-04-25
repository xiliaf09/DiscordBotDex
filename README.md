<<<<<<< HEAD
# Discord Bot Dex

Un bot Discord qui surveille les nouveaux tokens sur les blockchains Base et Solana via Dexscreener.

## Fonctionnalités

- Surveillance automatique des nouveaux tokens sur Base et Solana
- Notifications en temps réel dans un canal Discord
- Commandes pour activer/désactiver le monitoring par chaîne
- Commande pour afficher le dernier token détecté

## Commandes

- `!test` - Vérifie que le bot fonctionne
- `!lasttoken` - Affiche le dernier token détecté
- `!baseon` - Active le monitoring pour Base
- `!baseoff` - Désactive le monitoring pour Base
- `!solanaon` - Active le monitoring pour Solana
- `!solanaoff` - Désactive le monitoring pour Solana
- `!status` - Affiche le statut du monitoring pour chaque chaîne

## Installation

1. Clonez ce dépôt
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Créez un fichier `.env` basé sur `.env.example` et remplissez les variables :
   - `DISCORD_TOKEN` : Votre token de bot Discord
   - `CHANNEL_ID` : L'ID du canal Discord pour les notifications

4. Lancez le bot :
   ```bash
   python bot.py
   ```

## Déploiement

Le bot peut être déployé sur Railway.app pour un fonctionnement 24/7. 
=======
# Base Blockchain Token Monitor Bot

A Discord bot that monitors and notifies about new tokens on the Base blockchain using Dexscreener's API.

## Features

- Monitors new tokens on Base blockchain (chainId: 8453)
- Sends notifications to a specified Discord channel
- Persists seen tokens to avoid duplicate notifications
- Includes detailed token information and Dexscreener links
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- A Discord account and server
- A Discord bot token
- A Discord channel ID

## Setup Instructions

1. **Create a Discord Bot**
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Go to the "Bot" section and click "Add Bot"
   - Under "Privileged Gateway Intents", enable:
     - PRESENCE INTENT
     - SERVER MEMBERS INTENT
     - MESSAGE CONTENT INTENT
   - Copy the bot token (you'll need this later)

2. **Invite the Bot to Your Server**
   - Go to the "OAuth2" → "URL Generator" section
   - Select the following scopes:
     - `bot`
     - `applications.commands`
   - Select the following bot permissions:
     - `Send Messages`
     - `Embed Links`
     - `Read Message History`
   - Copy the generated URL and open it in your browser
   - Select your server and authorize the bot

3. **Get Your Channel ID**
   - In Discord, enable Developer Mode (User Settings → Advanced → Developer Mode)
   - Right-click on your target channel and select "Copy ID"

4. **Set Up Environment Variables**
   Create a `.env` file in the project root with:
   ```
   DISCORD_TOKEN=your_bot_token_here
   CHANNEL_ID=your_channel_id_here
   ```

5. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Run the Bot**
   ```bash
   python bot.py
   ```

## Deployment Options

### Heroku
1. Create a new Heroku app
2. Set the environment variables in Heroku's dashboard
3. Deploy using Git or Heroku CLI
4. Enable the worker dyno

### Railway
1. Create a new Railway project
2. Connect your GitHub repository
3. Set the environment variables
4. Deploy

### VPS
1. Set up a Linux server (Ubuntu recommended)
2. Install Python and required dependencies
3. Clone the repository
4. Set up environment variables
5. Run the bot using a process manager like `pm2` or `systemd`

## Logging

The bot logs all activities to both console and `bot.log` file. Check this file for debugging information.

## Error Handling

The bot includes comprehensive error handling for:
- API rate limits
- Network issues
- Invalid responses
- Discord connection problems

## License

MIT License 
>>>>>>> 0d68e3ad1bd7740dfe677417200ac73a71980361
