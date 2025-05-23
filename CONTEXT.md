# Clanker Sniper Bot - Documentation Complète

## 📊 API Clanker

### Endpoints Principaux
```python
BASE_URL = "https://api.clanker.com/v1"

ENDPOINTS = {
    "fid_info": f"{BASE_URL}/fid/",  # Info sur un FID spécifique
    "fid_activity": f"{BASE_URL}/fid/activity/",  # Activité d'un FID
    "token_info": f"{BASE_URL}/token/",  # Info sur un token
    "pool_info": f"{BASE_URL}/pool/",  # Info sur une pool
    "price_info": f"{BASE_URL}/price/"  # Info sur les prix
}
```

### Structure des Données
```python
# Réponse API FID
FID_RESPONSE = {
    "fid": "12345",
    "username": "example",
    "followers": 1000,
    "following": 500,
    "verifications": ["verified", "developer"],
    "activity_score": 0.85
}

# Réponse API Token
TOKEN_RESPONSE = {
    "address": "0x123...",
    "name": "Example Token",
    "symbol": "EXT",
    "liquidity": "10.5",
    "holders": 100,
    "price": "0.0001",
    "creator_fid": "12345"
}
```

## 🤖 Système de Sniping

### 1. Surveillance des FIDs
```python
# Configuration de surveillance
WATCHED_FIDS = {
    "12345",  # FID du créateur
    "67890",  # FID de l'influencer
}

# Critères de surveillance
FID_CRITERIA = {
    "min_followers": 1000,
    "min_activity_score": 0.7,
    "required_verifications": ["verified"]
}
```

### 2. Détection des Tokens
```python
# Critères de détection
TOKEN_CRITERIA = {
    "min_liquidity": "1",  # ETH
    "max_liquidity": "100",  # ETH
    "min_holders": 10,
    "max_holders": 1000,
    "min_price": "0.000001",  # ETH
    "max_price": "0.1"  # ETH
}
```

### 3. Logique de Sniping
```python
# Workflow de sniping
SNIPE_WORKFLOW = {
    "1. Détection": "Surveillance des FIDs et détection des nouveaux tokens",
    "2. Vérification": "Vérification des critères (liquidité, holders, etc.)",
    "3. Analyse": "Analyse du token et de son potentiel",
    "4. Exécution": "Exécution du sniping si tous les critères sont remplis",
    "5. Suivi": "Suivi du token et gestion de la position"
}
```

## 📱 Intégration Telegram

### 1. Configuration du Bot
```python
# Configuration Telegram
TELEGRAM_CONFIG = {
    "bot_token": "YOUR_BOT_TOKEN",
    "admin_chat_id": "YOUR_CHAT_ID",
    "alert_chat_id": "ALERT_CHAT_ID"
}
```

### 2. Types d'Alertes
```python
# Alertes Telegram
ALERT_TYPES = {
    "NEW_TOKEN": "🔔 Nouveau token détecté",
    "SNIPE_ATTEMPT": "🎯 Tentative de sniping",
    "SNIPE_SUCCESS": "✅ Sniping réussi",
    "SNIPE_FAILED": "❌ Sniping échoué",
    "PRICE_ALERT": "📊 Alerte de prix",
    "ERROR_ALERT": "⚠️ Erreur système"
}
```

### 3. Format des Messages
```python
# Format des messages
MESSAGE_FORMATS = {
    "NEW_TOKEN": """
🔔 Nouveau Token Détecté
Token: {name} ({symbol})
Créateur: {creator}
Liquidité: {liquidity} ETH
Prix: {price} ETH
    """,
    
    "SNIPE_SUCCESS": """
✅ Sniping Réussi
Token: {name} ({symbol})
Montant: {amount} ETH
Prix: {price} ETH
Profit: {profit} ETH
    """
}
```

## 🔄 Workflow Complet

### 1. Initialisation
```python
# Étapes d'initialisation
INIT_STEPS = {
    "1. Chargement": "Chargement de la configuration et des variables d'environnement",
    "2. Connexion": "Connexion à l'API Clanker et Telegram",
    "3. Vérification": "Vérification des FIDs surveillés",
    "4. Démarrage": "Démarrage des services de surveillance"
}
```

### 2. Surveillance Continue
```python
# Boucle de surveillance
MONITORING_LOOP = {
    "1. Vérification FIDs": "Vérification des activités des FIDs surveillés",
    "2. Détection Tokens": "Détection des nouveaux tokens",
    "3. Analyse": "Analyse des tokens selon les critères",
    "4. Alerte": "Envoi d'alertes Telegram si nécessaire",
    "5. Sniping": "Exécution du sniping si conditions remplies"
}
```

### 3. Gestion des Erreurs
```python
# Gestion des erreurs
ERROR_HANDLING = {
    "API_ERROR": "Tentative de reconnexion à l'API",
    "TELEGRAM_ERROR": "Tentative de renvoi des messages",
    "SNIPE_ERROR": "Annulation et rapport d'erreur",
    "NETWORK_ERROR": "Attente et nouvelle tentative"
}
```

## ⚙️ Optimisations

### 1. Performance
```python
# Optimisations de performance
PERFORMANCE_OPTIMIZATIONS = {
    "CACHE": "Mise en cache des données FID",
    "BATCH_REQUESTS": "Requêtes groupées à l'API",
    "ASYNC": "Utilisation de requêtes asynchrones",
    "RATE_LIMITING": "Gestion des limites d'API"
}
```

### 2. Sécurité
```python
# Mesures de sécurité
SECURITY_MEASURES = {
    "API_KEYS": "Stockage sécurisé des clés API",
    "WALLET": "Protection de la clé privée",
    "VALIDATION": "Validation des données",
    "LOGGING": "Journalisation sécurisée"
}
```

## 📈 Monitoring et Analytics

### 1. Métriques
```python
# Métriques de suivi
METRICS = {
    "SNIPE_SUCCESS_RATE": "Taux de succès des snipes",
    "AVERAGE_PROFIT": "Profit moyen par snipe",
    "REACTION_TIME": "Temps de réaction moyen",
    "API_LATENCY": "Latence de l'API"
}
```

### 2. Rapports
```python
# Types de rapports
REPORTS = {
    "DAILY": "Rapport quotidien des activités",
    "PERFORMANCE": "Rapport de performance",
    "ERRORS": "Rapport d'erreurs",
    "PROFIT": "Rapport de profit"
}
```

## 🔧 Dépannage

### 1. Erreurs Courantes
```python
# Erreurs et solutions
COMMON_ERRORS = {
    "API_CONNECTION": "Vérifier la connexion internet et les clés API",
    "TELEGRAM_CONNECTION": "Vérifier le token du bot et la connexion",
    "SNIPE_FAILED": "Vérifier la liquidité et les paramètres de gas",
    "RATE_LIMIT": "Ajuster les délais entre les requêtes"
}
```

### 2. Solutions
```python
# Solutions aux problèmes
SOLUTIONS = {
    "API_ISSUE": "Utiliser un backup API key",
    "TELEGRAM_ISSUE": "Envoyer les alertes par email",
    "SNIPE_ISSUE": "Ajuster les paramètres de sniping",
    "PERFORMANCE_ISSUE": "Optimiser les requêtes API"
}
```

## 📚 Ressources

### 1. Documentation
- [API Clanker](https://docs.clanker.com)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Uniswap V3](https://docs.uniswap.org)

### 2. Outils
- [Etherscan](https://etherscan.io)
- [DexScreener](https://dexscreener.com)
- [Etherscan Gas Tracker](https://etherscan.io/gastracker)

### 3. Communautés
- [Discord Clanker](https://discord.gg/clanker)
- [Telegram Community](https://t.me/clankercommunity)
- [GitHub Issues](https://github.com/clanker/issues) 