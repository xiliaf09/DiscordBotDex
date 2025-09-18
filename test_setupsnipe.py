#!/usr/bin/env python3
"""
Script de test pour vérifier la commande setupsnipe
"""

import os
import sys
import asyncio
import sqlite3

# Ajouter le répertoire courant au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_structure():
    """Teste la structure de la base de données"""
    print("🔍 Test de la structure de la base de données...")
    
    try:
        conn = sqlite3.connect('snipes.db')
        c = conn.cursor()
        
        # Vérifier la structure de active_snipes
        c.execute("PRAGMA table_info(active_snipes)")
        columns = c.fetchall()
        print(f"📋 Colonnes dans active_snipes: {columns}")
        
        # Vérifier la structure de tracked_addresses
        c.execute("PRAGMA table_info(tracked_addresses)")
        columns = c.fetchall()
        print(f"📋 Colonnes dans tracked_addresses: {columns}")
        
        # Tester l'insertion d'une adresse trackée
        test_address = "0x38B3890A0C0983bE825E353b809A96aC4fA0077e"
        c.execute("INSERT OR IGNORE INTO tracked_addresses (address) VALUES (?)", (test_address,))
        
        # Tester l'insertion d'un snipe
        c.execute("""
            INSERT OR REPLACE INTO active_snipes 
            (tracked_address, snipe_amount_eth, is_active) 
            VALUES (?, ?, ?)
        """, (test_address, 0.001, 1))
        
        # Vérifier l'insertion
        c.execute("SELECT * FROM active_snipes WHERE tracked_address = ?", (test_address,))
        result = c.fetchone()
        print(f"✅ Snipe inséré avec succès: {result}")
        
        # Vérifier la récupération
        c.execute("SELECT * FROM active_snipes WHERE tracked_address = ? AND is_active = 1", (test_address,))
        result = c.fetchone()
        print(f"✅ Snipe récupéré avec succès: {result}")
        
        conn.commit()
        conn.close()
        
        print("🎉 Tous les tests de base de données sont passés !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de base de données: {e}")
        return False

def test_database_manager():
    """Teste la classe DatabaseManager"""
    print("\n🔍 Test de la classe DatabaseManager...")
    
    try:
        # Import dynamique pour éviter les erreurs de config
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot", "bot.py")
        bot_module = importlib.util.module_from_spec(spec)
        
        # Mock des variables d'environnement nécessaires
        os.environ['DATABASE_URL'] = 'sqlite:///snipes.db'
        
        spec.loader.exec_module(bot_module)
        
        # Créer une instance de DatabaseManager
        db_manager = bot_module.DatabaseManager()
        
        # Tester l'ajout d'une adresse trackée
        test_address = "0x38B3890A0C0983bE825E353b809A96aC4fA0077e"
        db_manager.add_tracked_address(test_address)
        print(f"✅ Adresse trackée ajoutée: {test_address}")
        
        # Tester l'ajout d'un snipe
        db_manager.add_active_snipe(test_address, 0.001)
        print(f"✅ Snipe ajouté: {test_address} - 0.001 ETH")
        
        # Tester la récupération du snipe
        snipe = db_manager.get_snipe_for_address(test_address)
        print(f"✅ Snipe récupéré: {snipe}")
        
        # Tester la liste des snipes actifs
        snipes = db_manager.get_active_snipes()
        print(f"✅ Snipes actifs: {snipes}")
        
        print("🎉 Tous les tests de DatabaseManager sont passés !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de DatabaseManager: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Début des tests de la commande setupsnipe...")
    
    # Test 1: Structure de base de données
    test1_passed = test_database_structure()
    
    # Test 2: DatabaseManager
    test2_passed = test_database_manager()
    
    if test1_passed and test2_passed:
        print("\n🎉 Tous les tests sont passés ! La commande setupsnipe devrait fonctionner.")
    else:
        print("\n❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
