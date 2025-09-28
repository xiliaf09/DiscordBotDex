# 🎯 Système de Sniping Automatique $DAU sur Doppler

Ce guide explique comment configurer le sniping automatique du token $DAU dès qu'il est déployé sur Doppler.

## 📋 Prérequis

1. **Bot Discord** configuré et fonctionnel
2. **Bot Telegram** avec API 0x configuré
3. **Wallet** avec ETH sur Base
4. **Variables d'environnement** configurées

## 🚀 Configuration Rapide

### 1. Configuration du Bot Discord

Ajoutez ces variables d'environnement à votre bot Discord :

```bash
# Configuration du snipe automatique
DOPPLER_SNIPE_ENABLED=true
DOPPLER_SNIPE_TICKER=DAU
DOPPLER_SNIPE_AMOUNT=0.1

# URL du webhook Telegram (à remplacer par votre URL)
TELEGRAM_WEBHOOK_URL=http://votre-serveur:3000/webhook/snipe
TELEGRAM_CHAT_ID=votre_chat_id
```

### 2. Configuration du Bot Telegram

Dans le dossier `tgbotv4-master`, ajoutez Express aux dépendances :

```bash
npm install express
```

### 3. Démarrage du Serveur Webhook

```bash
cd tgbotv4-master
npm run webhook
```

Le serveur webhook sera accessible sur `http://localhost:3000`

## ⚙️ Commandes Discord Disponibles

### Activer le Sniper $DAU
```
!snipedau [montant]
```
- Active le sniping automatique pour $DAU
- Montant optionnel (défaut: 0.1 ETH)

### Désactiver le Sniper
```
!snipedauoff
```

### Voir la Configuration
```
!snipedauconfig
```

## 🔧 Configuration Avancée

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `DOPPLER_SNIPE_ENABLED` | Active/désactive le sniper | `false` |
| `DOPPLER_SNIPE_TICKER` | Ticker à surveiller | `DAU` |
| `DOPPLER_SNIPE_AMOUNT` | Montant ETH pour le snipe | `0.1` |
| `TELEGRAM_WEBHOOK_URL` | URL du webhook Telegram | - |
| `TELEGRAM_CHAT_ID` | ID du chat Telegram | - |

### Endpoints Webhook Disponibles

#### POST `/webhook/snipe`
Déclenche un snipe automatique

**Body:**
```json
{
  "action": "snipe",
  "token_address": "0x...",
  "amount_eth": 0.1,
  "platform": "doppler",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET `/health`
Statut du serveur webhook

#### GET `/balance/eth`
Solde ETH du wallet

#### POST `/test/buy`
Test d'achat manuel

## 🔄 Flux de Fonctionnement

1. **Détection** : Le bot Discord surveille les déploiements Doppler
2. **Filtrage** : Vérifie si le ticker correspond à $DAU
3. **Alerte** : Envoie une alerte spéciale dans Discord
4. **Webhook** : Envoie une requête au bot Telegram
5. **Snipe** : Le bot Telegram exécute l'achat automatiquement
6. **Confirmation** : Retourne le résultat au bot Discord

## 🛡️ Sécurité

- **Validation** : Toutes les adresses et montants sont validés
- **Limites** : Montant minimum de 0.00001 ETH
- **Slippage** : 2% par défaut pour éviter les échecs
- **Logs** : Toutes les transactions sont loggées

## 🧪 Tests

### Test du Webhook
```bash
curl -X POST http://localhost:3000/webhook/snipe \
  -H "Content-Type: application/json" \
  -d '{
    "action": "snipe",
    "token_address": "0x1234567890123456789012345678901234567890",
    "amount_eth": 0.01,
    "platform": "doppler"
  }'
```

### Test de Santé
```bash
curl http://localhost:3000/health
```

### Test de Solde
```bash
curl http://localhost:3000/balance/eth
```

## 📊 Monitoring

### Logs Discord
- Alerte spéciale quand $DAU est détecté
- Statut du snipe (en cours, réussi, échec)
- Lien vers la transaction

### Logs Telegram
- Démarrage du snipe
- Résultat de la transaction
- Hash de la transaction

### Logs Webhook
- Requêtes reçues
- Erreurs de validation
- Performances des transactions

## 🚨 Dépannage

### Le sniper ne se déclenche pas
1. Vérifiez `DOPPLER_SNIPE_ENABLED=true`
2. Vérifiez que le ticker correspond exactement
3. Vérifiez les logs Discord

### Erreur webhook
1. Vérifiez l'URL du webhook
2. Vérifiez que le serveur webhook est démarré
3. Vérifiez les logs du serveur webhook

### Échec de transaction
1. Vérifiez le solde ETH
2. Vérifiez la liquidité du token
3. Vérifiez les paramètres de slippage

## 📈 Optimisations

### Performance
- Détection en temps réel via WebSocket
- Validation rapide des paramètres
- Exécution parallèle des vérifications

### Fiabilité
- Reconnexion automatique en cas de perte de connexion
- Retry automatique en cas d'échec
- Fallback sur les données de transaction

### Sécurité
- Validation stricte des adresses
- Limites de montant configurables
- Logs détaillés pour audit

## 🎯 Utilisation

1. **Activez le sniper** : `!snipedau 0.1`
2. **Surveillez les alertes** : Le bot enverra une alerte spéciale quand $DAU sera détecté
3. **Vérifiez les transactions** : Utilisez les liens BaseScan pour vérifier les achats
4. **Désactivez si nécessaire** : `!snipedauoff`

Le système est maintenant prêt à sniper automatiquement $DAU dès qu'il sera déployé sur Doppler ! 🚀 