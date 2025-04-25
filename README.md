# Discord DexScreener Bot

Un bot Discord qui surveille les nouveaux tokens sur Base et Solana via DexScreener, et suit les mentions de crypto-monnaies par Donald Trump sur Truth Social.

## Fonctionnalités

- Surveillance en temps réel des nouveaux tokens sur Base et Solana
- Notifications Discord pour les nouveaux tokens détectés
- Surveillance des posts de Trump mentionnant des crypto-monnaies
- Commandes pour activer/désactiver la surveillance par chaîne
- Commande pour afficher le dernier token détecté
- Commande de test pour vérifier le bon fonctionnement du bot

## Commandes

- `!baseon` - Activer la surveillance de Base
- `!baseoff` - Désactiver la surveillance de Base
- `!solanaon` - Activer la surveillance de Solana
- `!solanaoff` - Désactiver la surveillance de Solana
- `!status` - Afficher le statut de surveillance des chaînes
- `!lasttoken` - Afficher le dernier token détecté
- `!test` - Tester le bon fonctionnement du bot

## Configuration

1. Créer un fichier `.env` avec les variables suivantes :
```
DISCORD_TOKEN=votre_token_discord
CHANNEL_ID=id_du_canal_discord
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancer le bot :
```bash
python bot.py
```

## Déploiement sur Railway

1. Connectez votre compte Railway à GitHub
2. Créez un nouveau projet depuis ce dépôt
3. Ajoutez les variables d'environnement dans les paramètres du projet
4. Railway déploiera automatiquement le bot

## Maintenance

- Les tokens vus sont stockés dans `seen_tokens.json`
- Les logs sont écrits dans `bot.log`
- Le bot garde en mémoire les 100 derniers posts de Trump vérifiés
