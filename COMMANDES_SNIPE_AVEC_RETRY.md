# 🎯 Commandes de Snipe avec Retry

## 📋 **Nouvelles Fonctionnalités**

### ✨ **Système de Retry Automatique**
- **Nombre de tentatives configurable** : De 1 à 10 tentatives
- **Délai entre tentatives** : 1 seconde automatique
- **Gestion intelligente des échecs** : Retry automatique en cas d'échec de liquidité

---

## 🚀 **Commandes Mises à Jour**

### 1. **`!setupsnipe <adresse> <montant> <tentatives>`**
Configure un snipe avec un nombre de tentatives personnalisé.

**Paramètres :**
- `<adresse>` : Adresse Ethereum à tracker (0x...)
- `<montant>` : Montant en ETH à investir
- `<tentatives>` : Nombre de tentatives (1-10, par défaut: 1)

**Exemples :**
```
!setupsnipe 0x3883890A0C0983bE825E353b809A96aC4fA0077e 0.001 5
!setupsnipe 0x1234...5678 0.005 3
!setupsnipe 0xabcd...efgh 0.01 1
```

**Réponse :**
```
✅ Snipe configuré avec succès !
**Adresse trackée:** `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
**Montant:** 0.001 ETH
**Tentatives:** 5
**Wallet de sniping:** `0x...`

Le bot achètera automatiquement 0.001 ETH du token dès que cette adresse déploiera un nouveau clanker.
En cas d'échec, le bot réessaiera jusqu'à 5 fois avec un délai d'1 seconde entre chaque tentative.
```

### 2. **`!listsnipes`** (Mise à jour)
Affiche maintenant le nombre de tentatives configuré pour chaque snipe.

**Exemple de réponse :**
```
🎯 Snipes Actifs
1 snipe(s) actif(s)

Adresse: `0x3883890A0C0983bE825E353b809A96aC4fA0077e`
**Montant:** 0.001 ETH
**Tentatives:** 5
**Créé:** 2025-09-18 21:42:13.572912
```

---

## 🔄 **Fonctionnement du Retry**

### **Scénario d'Exécution :**

1. **Détection d'un déploiement V4** par une adresse trackée
2. **Lancement du snipe automatique** avec le nombre de tentatives configuré
3. **Tentative 1** : Exécution du swap
   - ✅ **Succès** → Transaction confirmée, snipe terminé
   - ❌ **Échec** → Attente de 1 seconde, passage à la tentative 2
4. **Tentative 2** : Nouvelle exécution du swap
   - ✅ **Succès** → Transaction confirmée, snipe terminé
   - ❌ **Échec** → Attente de 1 seconde, passage à la tentative 3
5. **...** (jusqu'au nombre maximum de tentatives)
6. **Dernière tentative** : Si échec, affichage de l'erreur finale

### **Messages Discord en Temps Réel :**

#### **Début du Snipe :**
```
🎯 Snipe Automatique en Cours
Exécution du snipe configuré pour l'adresse trackée

Token: etest (etest)
Montant: 0.001 ETH
Tentatives: 5
Adresse Trackée: 0x3883890A0C0983bE825E353b809A96aC4fA0077e
Contract: 0x77E548985A539FCb5400B9eD6B2aeea4a6d52B07
```

#### **Tentative en Cours :**
```
🎯 Snipe Automatique en Cours
Exécution du snipe configuré pour l'adresse trackée (Tentative 3/5)

Token: etest (etest)
Montant: 0.001 ETH
Tentatives: 5
Adresse Trackée: 0x3883890A0C0983bE825E353b809A96aC4fA0077e
Contract: 0x77E548985A539FCb5400B9eD6B2aeea4a6d52B07
```

#### **Succès :**
```
✅ Snipe Réussi !
Snipe automatique exécuté avec succès (Tentative 3/5)

Token: etest (etest)
Montant: 0.001 ETH
Tentative: 3/5
Transaction: 0x1234...5678
Tokens Achetés: 1000000 wei
ETH Vendus: 1000000000000000 wei

[Voir Transaction] (bouton)
```

#### **Échec Final :**
```
❌ Échec du Snipe
Le snipe automatique a échoué après 5 tentatives

Token: etest (etest)
Montant: 0.001 ETH
Tentatives: 5
Dernière Erreur: Insufficient liquidity for this trade
```

---

## 🎯 **Cas d'Usage Recommandés**

### **1 tentative (par défaut) :**
- Tokens avec liquidité stable
- Snipes rapides sans retry
- Économie de gas

### **3-5 tentatives :**
- Tokens récemment déployés
- Liquidité qui se stabilise progressivement
- **Recommandé pour la plupart des cas**

### **5-10 tentatives :**
- Tokens très récents
- Liquidité très instable
- Snipes agressifs

---

## ⚠️ **Limitations et Considérations**

### **Limites :**
- **Maximum 10 tentatives** par snipe
- **Délai fixe de 1 seconde** entre chaque tentative
- **Pas de backoff exponentiel** (délai constant)

### **Considérations :**
- **Gas fees** : Chaque tentative consomme du gas
- **Temps total** : 10 tentatives = ~10 secondes maximum
- **Liquidité** : Le retry ne garantit pas le succès si la liquidité reste insuffisante

---

## 🔧 **Migration Automatique**

La base de données est automatiquement migrée pour inclure le champ `max_attempts` :
- **Nouveaux snipes** : Utilisent le nombre de tentatives spécifié
- **Anciens snipes** : Utilisent 1 tentative par défaut
- **Migration transparente** : Aucune action requise

---

## 📊 **Logs et Monitoring**

### **Logs de Console :**
```
🎯 Début du snipe automatique: 0.001 ETH -> 0x77E5... (etest) - 5 tentatives max
🔄 Tentative 1/5 du snipe automatique
⚠️ Tentative 1/5 échouée: Insufficient liquidity for this trade
⏳ Attente de 1 seconde avant la tentative 2
🔄 Tentative 2/5 du snipe automatique
✅ Snipe automatique réussi à la tentative 2: 0x1234...5678
```

### **Monitoring Discord :**
- **Messages en temps réel** pour chaque tentative
- **Statut visuel** avec embeds colorés
- **Boutons d'action** pour voir les transactions

---

## 🚀 **Exemple Complet**

```bash
# Configuration d'un snipe avec 5 tentatives
!setupsnipe 0x3883890A0C0983bE825E353b809A96aC4fA0077e 0.001 5

# Vérification des snipes actifs
!listsnipes

# Résultat attendu lors d'un déploiement :
# 1. Détection du token V4
# 2. Lancement du snipe avec 5 tentatives
# 3. Tentative 1: Échec (liquidité insuffisante)
# 4. Attente 1 seconde
# 5. Tentative 2: Succès ✅
# 6. Transaction confirmée sur Basescan
```

---

## 🎉 **Avantages du Système de Retry**

1. **Résilience** : Gestion automatique des échecs temporaires
2. **Flexibilité** : Nombre de tentatives personnalisable
3. **Transparence** : Messages en temps réel sur Discord
4. **Efficacité** : Délai optimisé de 1 seconde
5. **Sécurité** : Limite de 10 tentatives maximum
6. **Compatibilité** : Migration automatique de la base de données

Le système de retry améliore considérablement les chances de succès des snipes automatiques, particulièrement pour les tokens récemment déployés où la liquidité peut être instable au début.
