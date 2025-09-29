# Configuration des Appels Twilio pour Solana

## 📱 Vue d'ensemble

Ce système vous permet de recevoir des appels téléphoniques automatiques lorsque des adresses Solana que vous trackez effectuent des transactions importantes.

## ⚙️ Configuration

### 1. Variables d'Environnement

Ajoutez ces variables à votre fichier `.env` :

```bash
# Configuration Twilio (partagée avec les alertes volume)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
YOUR_PHONE_NUMBER=+0987654321

# Configuration Solana Twilio
SOLANA_CALL_ENABLED=true                    # Activer/désactiver les appels Solana
SOLANA_CALL_MIN_AMOUNT=0                    # Montant minimum pour déclencher un appel
```

### 2. Paramètres de Configuration

#### `SOLANA_CALL_ENABLED`
- `true` : Active les appels téléphoniques pour les alertes Solana
- `false` : Désactive les appels téléphoniques pour les alertes Solana
- **Défaut** : `true`

#### `SOLANA_CALL_MIN_AMOUNT`
- `0` : Appeler pour tous les mouvements (par défaut)
- `1.5` : Appeler seulement pour les mouvements ≥ 1.5 SOL/tokens
- `100` : Appeler seulement pour les mouvements ≥ 100 tokens
- **Défaut** : `0`

## 🎯 Types de Transactions Surveillées

Les appels sont déclenchés pour tous les types de transactions détectées :
- `token_transfer` : Transfert de tokens
- `dex_swap` : Échange sur DEX
- `stake` : Mise en stake
- `unstake` : Retrait de stake
- `nft_transfer` : Transfert de NFT
- Et autres types de transactions

## 📞 Messages d'Appel

### Format du Message
```
"Solana alert! Tracked address [8 premiers caractères]... has performed a [type de transaction] transaction for [montant]. This is an alert from your Solana tracker bot."
```

### Exemples de Messages
- **Avec montant** : "Solana alert! Tracked address 9WzDXwB... has performed a token_transfer transaction for 5.5 SOL. This is an alert from your Solana tracker bot."
- **Sans montant** : "Solana alert! Tracked address 9WzDXwB... has performed a stake transaction. This is an alert from your Solana tracker bot."

## 🧪 Test de l'Intégration

Utilisez le script de test fourni :

```bash
python test_solana_twilio_integration.py
```

Ce script :
1. Vérifie la configuration Twilio
2. Teste le parsing des montants
3. Permet de faire un appel de test (optionnel)

## 📋 Commandes Discord

### Gestion des Adresses Solana
```
!soladd 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM "Wallet Principal"
!sollist
!solremove 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
!solactivity [address] [limit]
!solsettings 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM 1.5 all
!soltest
```

### Contrôle des Appels Twilio Solana
```
!solcallon                    # Active les appels téléphoniques
!solcalloff                   # Désactive les appels téléphoniques
!solcallset 1.5              # Définit le seuil à 1.5 (SOL/tokens)
!solcallstatus               # Affiche le statut actuel
!solcalltest                 # Teste un appel téléphonique
```

### Exemples d'Utilisation

**Activer les appels pour tous les mouvements :**
```
!solcallon
!solcallset 0
```

**Activer les appels seulement pour les gros mouvements :**
```
!solcallon
!solcallset 10
```

**Désactiver temporairement les appels :**
```
!solcalloff
```

**Vérifier la configuration :**
```
!solcallstatus
```

## 🔧 Dépannage

### Problèmes Courants

1. **Pas d'appel reçu**
   - Vérifiez que `SOLANA_CALL_ENABLED=true`
   - Vérifiez que `SOLANA_CALL_MIN_AMOUNT` n'est pas trop élevé
   - Vérifiez la configuration Twilio

2. **Trop d'appels**
   - Augmentez `SOLANA_CALL_MIN_AMOUNT` pour filtrer les petits montants
   - Désactivez avec `SOLANA_CALL_ENABLED=false`

3. **Erreurs Twilio**
   - Vérifiez que les crédits Twilio sont suffisants
   - Vérifiez que le numéro de téléphone est au format international

### Logs à Surveiller

Recherchez ces messages dans les logs :
- `[SOLANA TWILIO] Emergency call triggered` : Appel déclenché
- `[SOLANA TWILIO ERROR]` : Erreurs d'appel
- `[TWILIO] Solana emergency call initiated` : Appel initié avec succès

## 💡 Conseils d'Utilisation

1. **Seuils Recommandés**
   - Pour les gros traders : `SOLANA_CALL_MIN_AMOUNT=10`
   - Pour tous les mouvements : `SOLANA_CALL_MIN_AMOUNT=0`
   - Pour les très gros mouvements : `SOLANA_CALL_MIN_AMOUNT=100`

2. **Optimisation des Coûts**
   - Les appels Twilio ont un coût (environ $0.02-0.05 par appel)
   - Utilisez des seuils appropriés pour éviter les appels inutiles

3. **Sécurité**
   - Ne partagez jamais vos clés Twilio
   - Utilisez des variables d'environnement sécurisées

## 🔄 Intégration avec le Système Existant

Cette fonctionnalité s'intègre parfaitement avec :
- ✅ Alertes Discord existantes
- ✅ Système de tracking Solana existant
- ✅ Configuration Twilio partagée avec les alertes volume
- ✅ Base de données Solana existante

## 📊 Monitoring

Le système enregistre automatiquement :
- Tous les appels déclenchés
- Les erreurs d'appel
- Les tentatives d'appel ignorées (montant trop faible)
- Les statistiques d'utilisation

Consultez les logs pour surveiller l'activité et diagnostiquer les problèmes.
