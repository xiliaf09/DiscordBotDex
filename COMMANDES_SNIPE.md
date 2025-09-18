# 🎯 Commandes de Snipe - Bot Discord

## 📋 **Commandes Principales de Snipe**

### 🔧 **Configuration des Snipes**

#### `!setupsnipe <adresse> <montant>`
- **Description** : Configure un snipe automatique pour une adresse trackée
- **Paramètres** :
  - `<adresse>` : Adresse de l'utilisateur à tracker (ex: `0x1234...`)
  - `<montant>` : Montant en ETH à dépenser (ex: `0.001`)
- **Exemple** : `!setupsnipe 0x1234567890abcdef1234567890abcdef12345678 0.001`
- **Permissions** : Administrateur uniquement

#### `!cancelsnipe <adresse>`
- **Description** : Annule un snipe actif pour une adresse trackée
- **Paramètres** :
  - `<adresse>` : Adresse de l'utilisateur à ne plus tracker
- **Exemple** : `!cancelsnipe 0x1234567890abcdef1234567890abcdef12345678`
- **Permissions** : Administrateur uniquement

#### `!listsnipes`
- **Description** : Affiche la liste des snipes actifs
- **Exemple** : `!listsnipes`
- **Permissions** : Tous les utilisateurs

### 🧪 **Test de Snipe**

#### `!testsnipe <token> <montant>`
- **Description** : Teste un snipe sur un token spécifique
- **Paramètres** :
  - `<token>` : Adresse du token à acheter (ex: `0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69`)
  - `<montant>` : Montant en ETH à dépenser (ex: `0.0001`)
- **Exemple** : `!testsnipe 0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69 0.0001`
- **Permissions** : Administrateur uniquement

### 📊 **Gestion des Adresses Trackées**

#### `!trackdeploy <adresse>`
- **Description** : Ajoute une adresse à la liste des adresses trackées
- **Paramètres** :
  - `<adresse>` : Adresse à tracker
- **Exemple** : `!trackdeploy 0x1234567890abcdef1234567890abcdef12345678`
- **Permissions** : Administrateur uniquement

#### `!untrackdeploy <adresse>`
- **Description** : Retire une adresse de la liste des adresses trackées
- **Paramètres** :
  - `<adresse>` : Adresse à ne plus tracker
- **Exemple** : `!untrackdeploy 0x1234567890abcdef1234567890abcdef12345678`
- **Permissions** : Administrateur uniquement

#### `!listtracked`
- **Description** : Affiche la liste des adresses trackées
- **Exemple** : `!listtracked`
- **Permissions** : Tous les utilisateurs

## 🔄 **Comment ça fonctionne ?**

### 1. **Configuration d'un Snipe**
```
!trackdeploy 0x1234567890abcdef1234567890abcdef12345678
!setupsnipe 0x1234567890abcdef1234567890abcdef12345678 0.001
```

### 2. **Test d'un Snipe**
```
!testsnipe 0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69 0.0001
```

### 3. **Vérification des Snipes Actifs**
```
!listsnipes
```

### 4. **Annulation d'un Snipe**
```
!cancelsnipe 0x1234567890abcdef1234567890abcdef12345678
```

## ⚙️ **Configuration Requise**

### 🔑 **Variables d'Environnement**
- `ZEROX_API_KEY` : Clé API 0x (requise)
- `SNIPINGWALLETKEY` : Clé privée du wallet de sniping (requise)
- `BASE_RPC_URL` : URL RPC Base (requise)

### 💰 **Wallet de Sniping**
- Le wallet doit avoir suffisamment d'ETH pour les snipes
- La clé privée doit être configurée dans `SNIPINGWALLETKEY`

## 🎯 **Exemples d'Utilisation**

### **Snipe Automatique**
1. Track une adresse qui déploie souvent des tokens
2. Configure un snipe automatique
3. Le bot achètera automatiquement les nouveaux tokens

### **Snipe Manuel**
1. Utilise `!testsnipe` pour tester un token spécifique
2. Vérifie que le snipe fonctionne
3. Configure un snipe automatique si nécessaire

## ⚠️ **Important**

- **Permissions** : La plupart des commandes nécessitent des permissions d'administrateur
- **Montants** : Spécifiez toujours les montants en ETH (ex: 0.001 pour 0.001 ETH)
- **Adresses** : Utilisez des adresses Ethereum valides (0x...)
- **Test** : Toujours tester avec `!testsnipe` avant de configurer un snipe automatique

## 🚀 **Statut Actuel**

✅ **Bot fonctionnel** - Toutes les corrections appliquées
✅ **API 0x v2** - Intégration complète
✅ **Tests réussis** - 2 swaps réels effectués avec succès
✅ **Prêt pour production** - Toutes les fonctionnalités opérationnelles
