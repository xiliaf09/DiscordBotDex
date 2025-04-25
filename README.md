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