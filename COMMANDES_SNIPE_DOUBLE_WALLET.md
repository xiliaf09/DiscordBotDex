# 🎯 Commandes de Snipe avec Double Wallet et FID

## 📋 **Nouvelles Fonctionnalités**

### ✨ **Système de Double Wallet**
- **Wallet W1** : Configuration principale (SNIPINGWALLETKEY + ZEROX_API_KEY)
- **Wallet W2** : Configuration secondaire (SNIPINGWALLETKEY2 + ZEROX_API_KEY2)
- **Sélection du wallet** : Choix du wallet lors de la configuration du snipe

### ✨ **Snipe par FID**
- **Snipe par adresse** : Surveillance d'une adresse Ethereum spécifique
- **Snipe par FID** : Surveillance d'un FID (Farcaster ID) spécifique
- **Détection automatique** : Le bot détecte les déploiements par adresse ou par FID

---

## 🚀 **Commandes Mises à Jour**

### 1. **`!setupsnipe <adresse> <montant> <tentatives> <wallet>`**
Configure un snipe pour une adresse trackée avec un wallet spécifique.

**Paramètres :**
- `<adresse>` : Adresse Ethereum à tracker (0x...)
- `<montant>` : Montant en ETH à investir
- `<tentatives>` : Nombre de tentatives (1-10)
- `<wallet>` : Wallet à utiliser (W1 ou W2)

**Exemples :**
```
!setupsnipe 0x3883890A0C0983bE825E353b809A96aC4fA0077e 0.001 5 W1
!setupsnipe 0x1234...5678 0.005 3 W2
!setupsnipe 0xabcd...efgh 0.01 1 W1
```

**Réponse :**
```
✅ Snipe configuré avec succès !
**Adresse trackée:** `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
**Montant:** 0.001 ETH
**Tentatives:** 5
**Wallet:** W1 (`0x...`)

Le bot achètera automatiquement 0.001 ETH du token dès que cette adresse déploiera un nouveau clanker.
En cas d'échec, le bot réessaiera jusqu'à 5 fois avec un délai de 0.5 seconde entre chaque tentative.
```

### 2. **`!cancelsnipe <adresse> <wallet>`**
Annule un snipe actif pour une adresse trackée avec un wallet spécifique.

**Paramètres :**
- `<adresse>` : Adresse Ethereum trackée (0x...)
- `<wallet>` : Wallet utilisé (W1 ou W2)

**Exemples :**
```
!cancelsnipe 0x3883890A0C0983bE825E353b809A96aC4fA0077e W1
!cancelsnipe 0x1234...5678 W2
```

**Réponse :**
```
✅ Snipe annulé avec succès !
**Adresse:** `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
**Wallet:** W1
**Montant:** 0.001 ETH
```

### 3. **`!setupsnipefid <FID> <montant> <tentatives> <wallet>`** ⭐ **NOUVEAU**
Configure un snipe pour un FID tracké avec un wallet spécifique.

**Paramètres :**
- `<FID>` : FID (Farcaster ID) à tracker
- `<montant>` : Montant en ETH à investir
- `<tentatives>` : Nombre de tentatives (1-10)
- `<wallet>` : Wallet à utiliser (W1 ou W2)

**Exemples :**
```
!setupsnipefid 12345 0.001 5 W1
!setupsnipefid 67890 0.005 3 W2
!setupsnipefid 11111 0.01 1 W1
```

**Réponse :**
```
✅ Snipe FID configuré avec succès !
**FID tracké:** `12345`
**Montant:** 0.001 ETH
**Tentatives:** 5
**Wallet:** W1 (`0x...`)

Le bot achètera automatiquement 0.001 ETH du token dès que ce FID déploiera un nouveau clanker.
En cas d'échec, le bot réessaiera jusqu'à 5 fois avec un délai de 0.5 seconde entre chaque tentative.
```

### 4. **`!cancelsnipefid <FID> <wallet>`** ⭐ **NOUVEAU**
Annule un snipe actif pour un FID tracké avec un wallet spécifique.

**Paramètres :**
- `<FID>` : FID (Farcaster ID) tracké
- `<wallet>` : Wallet utilisé (W1 ou W2)

**Exemples :**
```
!cancelsnipefid 12345 W1
!cancelsnipefid 67890 W2
```

**Réponse :**
```
✅ Snipe FID annulé avec succès !
**FID:** `12345`
**Wallet:** W1
**Montant:** 0.001 ETH
```

### 5. **`!listsnipes`** (Mise à jour)
Affiche maintenant le wallet utilisé et le type de snipe pour chaque snipe actif.

**Exemple de réponse :**
```
🎯 Snipes Actifs
2 snipe(s) actif(s)

Adresse: `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
**Adresse:** `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
**Montant:** 0.001 ETH
**Tentatives:** 5
**Wallet:** W1
**Type:** address
**Créé:** 2025-09-18 21:42:13.572912

FID: `12345`
**FID:** `12345`
**Montant:** 0.005 ETH
**Tentatives:** 3
**Wallet:** W2
**Type:** fid
**Créé:** 2025-09-18 22:15:30.123456
```

---

## 🔧 **Configuration des Variables d'Environnement**

### **Variables Requises :**

#### **Wallet W1 (Principal) :**
```bash
SNIPINGWALLETKEY=0x...  # Clé privée du wallet W1
ZEROX_API_KEY=...       # Clé API 0x pour W1
```

#### **Wallet W2 (Secondaire) :**
```bash
SNIPINGWALLETKEY2=0x... # Clé privée du wallet W2
ZEROX_API_KEY2=...      # Clé API 0x pour W2
```

### **Migration Automatique :**
La base de données est automatiquement migrée pour inclure les nouveaux champs :
- **`wallet_id`** : W1 ou W2
- **`snipe_type`** : address ou fid
- **`tracked_fid`** : FID tracké (pour les snipes par FID)

---

## 🎯 **Fonctionnement du Système**

### **Détection des Déploiements :**

#### **Snipe par Adresse :**
1. **Détection** : Le bot surveille les déploiements V3/V4
2. **Vérification** : L'adresse du créateur correspond à l'adresse trackée
3. **Exécution** : Lancement du snipe avec le wallet configuré

#### **Snipe par FID :**
1. **Détection** : Le bot surveille les déploiements V3/V4
2. **Vérification** : Le FID du créateur correspond au FID tracké
3. **Exécution** : Lancement du snipe avec le wallet configuré

### **Sélection du Wallet :**
- **W1** : Utilise `SNIPINGWALLETKEY` + `ZEROX_API_KEY`
- **W2** : Utilise `SNIPINGWALLETKEY2` + `ZEROX_API_KEY2`
- **Validation** : Vérification que le wallet est configuré avant l'exécution

---

## 📊 **Messages Discord en Temps Réel**

### **Début du Snipe :**
```
🎯 Snipe Automatique en Cours
Exécution du snipe configuré pour Adresse: `0x3883890A0C0983bE825E353b809A96aC4fA0077e`

Token: etest (etest)
Montant: 0.001 ETH
Tentatives: 5
Wallet: W1
Type: address
Cible Trackée: `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
Contract: `0x77E548985A539FCb5400B9eD6B2aeea4a6d52B07`
```

### **Succès :**
```
✅ Snipe Réussi !
Snipe automatique exécuté avec succès (Tentative 2/5)

Token: etest (etest)
Montant: 0.001 ETH
Tentative: 2/5
Wallet: W1
Type: address
Transaction: 0x1234...5678
Tokens Achetés: 1000000 wei
ETH Vendus: 1000000000000000 wei

[Voir Transaction] (bouton)
```

### **Échec :**
```
❌ Échec du Snipe
Le snipe automatique a échoué après 5 tentatives

Token: etest (etest)
Montant: 0.001 ETH
Tentatives: 5
Wallet: W1
Type: address
Dernière Erreur: Insufficient liquidity for this trade
```

---

## 🎯 **Cas d'Usage Avancés**

### **Stratégie Multi-Wallet :**
```bash
# Snipe agressif avec W1
!setupsnipe 0x1234...5678 0.01 10 W1

# Snipe conservateur avec W2
!setupsnipe 0x1234...5678 0.005 3 W2

# Snipe par FID avec W1
!setupsnipefid 12345 0.001 5 W1
```

### **Gestion des Risques :**
- **W1** : Wallet principal pour les snipes importants
- **W2** : Wallet secondaire pour les snipes de test
- **Séparation** : Chaque wallet peut avoir des montants et tentatives différents

### **Surveillance Hybride :**
- **Adresse + FID** : Surveillance simultanée d'une adresse et d'un FID
- **Wallets différents** : Utilisation de W1 pour l'adresse et W2 pour le FID
- **Flexibilité** : Configuration indépendante pour chaque cible

---

## ⚠️ **Limitations et Considérations**

### **Limites :**
- **Maximum 10 tentatives** par snipe
- **Délai fixe de 0.5 seconde** entre chaque tentative
- **2 wallets maximum** (W1 et W2)

### **Considérations :**
- **Gas fees** : Chaque tentative consomme du gas
- **Configuration** : Les deux wallets doivent être configurés
- **API Keys** : Chaque wallet nécessite sa propre clé API 0x
- **Liquidité** : Le retry ne garantit pas le succès si la liquidité reste insuffisante

---

## 🚀 **Exemple Complet**

```bash
# Configuration des snipes
!setupsnipe 0x3883890A0C0983bE825E353b809A96aC4fA0077e 0.001 5 W1
!setupsnipefid 12345 0.005 3 W2

# Vérification
!listsnipes

# Résultat attendu lors d'un déploiement :
# 1. Détection du token V4 par l'adresse 0x3883...
# 2. Lancement du snipe avec W1 (5 tentatives)
# 3. Tentative 1: Échec (liquidité insuffisante)
# 4. Attente 0.5 seconde
# 5. Tentative 2: Succès ✅
# 6. Transaction confirmée sur Basescan avec W1

# OU

# 1. Détection du token V4 par le FID 12345
# 2. Lancement du snipe avec W2 (3 tentatives)
# 3. Tentative 1: Succès ✅
# 4. Transaction confirmée sur Basescan avec W2
```

---

## 🎉 **Avantages du Système Double Wallet + FID**

1. **Flexibilité** : Choix du wallet selon la stratégie
2. **Séparation des risques** : Wallets indépendants
3. **Surveillance hybride** : Adresse + FID simultanément
4. **Configuration granulaire** : Montants et tentatives différents par wallet
5. **Résilience** : Si un wallet échoue, l'autre peut continuer
6. **Transparence** : Messages détaillés avec wallet et type
7. **Compatibilité** : Migration automatique de la base de données

Le système double wallet avec snipe par FID offre une flexibilité maximale pour les stratégies de sniping avancées, permettant une gestion fine des risques et des opportunités.
