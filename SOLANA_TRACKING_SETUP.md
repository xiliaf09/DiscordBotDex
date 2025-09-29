# Configuration du Tracking Solana

Ce guide explique comment configurer le système de tracking des adresses Solana avec des notifications Discord.

## Prérequis

1. **QuickNode Solana** : Vous devez avoir un endpoint QuickNode pour Solana
2. **Discord Bot** : Le bot Discord doit être configuré et fonctionnel
3. **Python 3.8+** : Version Python compatible

## Configuration des Variables d'Environnement

Ajoutez ces variables à votre fichier `.env` :

```bash
# Solana Configuration (QuickNode)
SOLANA_RPC_URL=https://your-quicknode-solana-endpoint.com
SOLANA_WS_URL=wss://your-quicknode-solana-websocket.com
```

### Obtenir les URLs QuickNode

1. Connectez-vous à votre dashboard QuickNode
2. Sélectionnez votre endpoint Solana
3. Copiez l'URL RPC et l'URL WebSocket
4. Ajoutez-les à votre fichier `.env`

## Installation des Dépendances

Installez les nouvelles dépendances Solana :

```bash
pip install -r requirements.txt
```

Les nouvelles dépendances ajoutées :
- `solana==0.30.2`
- `solders==0.18.1`
- `websockets==12.0`

## Commandes Discord Disponibles

### Commandes Administrateur

#### Ajouter une adresse au tracking
```
!soladd <address> [nickname]
```
**Exemple :**
```
!soladd 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM "Wallet Principal"
```

#### Retirer une adresse du tracking
```
!solremove <address>
```
**Exemple :**
```
!solremove 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

#### Configurer les paramètres de notification
```
!solsettings <address> <min_amount> <notification_types>
```
**Exemple :**
```
!solsettings 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM 100 token_transfer,dex_swap
```

### Commandes Publiques

#### Lister les adresses trackées
```
!sollist
```

#### Voir l'activité récente
```
!solactivity [address] [limit]
```
**Exemples :**
```
!solactivity                                    # Toutes les adresses
!solactivity 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM  # Adresse spécifique
!solactivity 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM 20  # Avec limite
```

## Types de Notifications

Le système peut détecter et notifier les types de transactions suivants :

- **`token_transfer`** : Transferts de tokens
- **`sol_transfer`** : Transferts de SOL
- **`dex_swap`** : Échanges sur les DEX (Raydium, Orca, etc.)
- **`unknown`** : Autres types de transactions

## Configuration des Notifications

### Montant Minimum
Définissez un montant minimum pour filtrer les notifications :
- `0` : Toutes les transactions
- `100` : Seulement les transactions ≥ 100 tokens

### Types de Notifications
Filtrez par type de transaction :
- `all` : Tous les types
- `token_transfer,dex_swap` : Seulement les transferts et swaps

## Base de Données

Le système utilise une base de données SQLite (`solana_tracking.db`) pour stocker :

- **Adresses trackées** : Liste des adresses surveillées
- **Historique des transactions** : Toutes les transactions détectées
- **Paramètres de notification** : Configuration par adresse

## Fonctionnement Technique

1. **WebSocket Connection** : Connexion en temps réel à QuickNode
2. **Account Subscriptions** : Surveillance des changements de comptes
3. **Transaction Analysis** : Analyse des transactions pour déterminer le type
4. **Notification Filtering** : Application des filtres configurés
5. **Discord Notifications** : Envoi des alertes via Discord

## Dépannage

### Erreurs Courantes

1. **"Error initializing Solana client"**
   - Vérifiez que `SOLANA_RPC_URL` est correct
   - Testez la connexion à QuickNode

2. **"Discord channel not found"**
   - Vérifiez que `DISCORD_CHANNEL_ID` est correct
   - Assurez-vous que le bot a accès au canal

3. **"Adresse Solana invalide"**
   - Vérifiez le format de l'adresse (32+ caractères)
   - Utilisez une adresse Solana valide

### Logs

Consultez les logs dans `bot.log` pour diagnostiquer les problèmes :
```bash
tail -f bot.log | grep -i solana
```

## Exemples d'Utilisation

### Tracking d'un Wallet Principal
```
!soladd 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM "Wallet Principal"
!solsettings 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM 50 all
```

### Tracking d'un Bot de Trading
```
!soladd 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU "Trading Bot"
!solsettings 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU 0 dex_swap
```

### Surveillance d'un Smart Contract
```
!soladd 11111111111111111111111111111111 "System Program"
!solsettings 11111111111111111111111111111111 0 all
```

## Support

Pour toute question ou problème :
1. Vérifiez les logs du bot
2. Testez la connexion QuickNode
3. Vérifiez les permissions Discord du bot
