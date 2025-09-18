#!/usr/bin/env python3
"""
Test final de la commande setupsnipe
"""

import sqlite3

def test_setupsnipe_logic():
    """Teste la logique de la commande setupsnipe"""
    print("🔍 Test de la logique setupsnipe...")
    
    try:
        conn = sqlite3.connect('snipes.db')
        c = conn.cursor()
        
        # Simuler la commande: !setupsnipe 0x38B3890A0C0983bE825E353b809A96aC4fA0077e 0.001
        tracked_address = "0x38B3890A0C0983bE825E353b809A96aC4fA0077e"
        eth_amount = 0.001
        
        print(f"🎯 Configuration du snipe pour {tracked_address} avec {eth_amount} ETH")
        
        # Étape 1: Vérifier si l'adresse est trackée
        c.execute("SELECT address FROM tracked_addresses WHERE address = ?", (tracked_address,))
        if not c.fetchone():
            print(f"❌ Adresse {tracked_address} n'est pas trackée")
            return False
        
        print(f"✅ Adresse {tracked_address} est trackée")
        
        # Étape 2: Vérifier s'il y a déjà un snipe actif
        c.execute("""
            SELECT id, tracked_address, snipe_amount_eth, created_at 
            FROM active_snipes 
            WHERE tracked_address = ? AND is_active = 1
        """, (tracked_address,))
        
        existing_snipe = c.fetchone()
        if existing_snipe:
            print(f"⚠️ Snipe existant trouvé: {existing_snipe}")
            # Désactiver l'ancien snipe
            c.execute("UPDATE active_snipes SET is_active = 0 WHERE tracked_address = ?", (tracked_address,))
            print("✅ Ancien snipe désactivé")
        
        # Étape 3: Créer le nouveau snipe
        c.execute("""
            INSERT INTO active_snipes 
            (tracked_address, snipe_amount_eth, is_active) 
            VALUES (?, ?, ?)
        """, (tracked_address, eth_amount, 1))
        
        print(f"✅ Nouveau snipe créé: {tracked_address} - {eth_amount} ETH")
        
        # Étape 4: Vérifier la création
        c.execute("""
            SELECT id, tracked_address, snipe_amount_eth, created_at 
            FROM active_snipes 
            WHERE tracked_address = ? AND is_active = 1
        """, (tracked_address,))
        
        new_snipe = c.fetchone()
        print(f"✅ Snipe vérifié: {new_snipe}")
        
        # Étape 5: Lister tous les snipes actifs
        c.execute("""
            SELECT id, tracked_address, snipe_amount_eth, created_at 
            FROM active_snipes 
            WHERE is_active = 1
        """)
        
        all_snipes = c.fetchall()
        print(f"📋 Tous les snipes actifs: {all_snipes}")
        
        conn.commit()
        conn.close()
        
        print("🎉 Test de la logique setupsnipe réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_cancelsnipe_logic():
    """Teste la logique de la commande cancelsnipe"""
    print("\n🔍 Test de la logique cancelsnipe...")
    
    try:
        conn = sqlite3.connect('snipes.db')
        c = conn.cursor()
        
        tracked_address = "0x38B3890A0C0983bE825E353b809A96aC4fA0077e"
        
        # Vérifier s'il y a un snipe actif
        c.execute("""
            SELECT id, tracked_address, snipe_amount_eth, created_at 
            FROM active_snipes 
            WHERE tracked_address = ? AND is_active = 1
        """, (tracked_address,))
        
        snipe = c.fetchone()
        if not snipe:
            print(f"❌ Aucun snipe actif trouvé pour {tracked_address}")
            return False
        
        print(f"✅ Snipe trouvé: {snipe}")
        
        # Désactiver le snipe
        c.execute("UPDATE active_snipes SET is_active = 0 WHERE tracked_address = ?", (tracked_address,))
        print(f"✅ Snipe désactivé pour {tracked_address}")
        
        # Vérifier la désactivation
        c.execute("""
            SELECT id, tracked_address, snipe_amount_eth, created_at 
            FROM active_snipes 
            WHERE tracked_address = ? AND is_active = 1
        """, (tracked_address,))
        
        if c.fetchone():
            print("❌ Le snipe est toujours actif")
            return False
        
        print("✅ Snipe correctement désactivé")
        
        conn.commit()
        conn.close()
        
        print("🎉 Test de la logique cancelsnipe réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test final des commandes de snipe...")
    
    # Test setupsnipe
    test1_passed = test_setupsnipe_logic()
    
    # Test cancelsnipe
    test2_passed = test_cancelsnipe_logic()
    
    if test1_passed and test2_passed:
        print("\n🎉 Tous les tests sont passés !")
        print("✅ La commande !setupsnipe devrait maintenant fonctionner dans Discord")
        print("✅ La commande !cancelsnipe devrait maintenant fonctionner dans Discord")
    else:
        print("\n❌ Certains tests ont échoué.")
