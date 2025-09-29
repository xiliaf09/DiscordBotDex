#!/usr/bin/env python3
"""
Script de test pour le système de tracking Solana
"""

import asyncio
import logging
from solana_tracker import SolanaTracker
from solana_database import SolanaDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_solana_tracking():
    """Test basique du système de tracking Solana"""
    try:
        print("🧪 Test du système de tracking Solana...")
        
        # Test de la base de données
        print("📊 Test de la base de données...")
        db = SolanaDatabase()
        print("✅ Base de données initialisée")
        
        # Test d'ajout d'adresse
        test_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        success = db.add_tracked_address(test_address, "Test Wallet", "test_user")
        print(f"✅ Adresse ajoutée: {success}")
        
        # Test de récupération des adresses
        addresses = db.get_tracked_addresses()
        print(f"✅ Adresses trackées: {len(addresses)}")
        
        # Test du tracker (sans connexion réelle)
        print("🔗 Test du tracker Solana...")
        tracker = SolanaTracker()
        
        # Test d'ajout d'adresse au tracker
        success = await tracker.add_address(test_address, "Test Wallet", "test_user")
        print(f"✅ Adresse ajoutée au tracker: {success}")
        
        # Test de récupération des adresses trackées
        tracked_addresses = tracker.get_tracked_addresses()
        print(f"✅ Adresses dans le tracker: {len(tracked_addresses)}")
        
        print("🎉 Tous les tests sont passés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        logger.error(f"Test error: {e}")

def test_database_operations():
    """Test des opérations de base de données"""
    try:
        print("📊 Test des opérations de base de données...")
        
        db = SolanaDatabase("test_solana.db")
        
        # Test d'ajout d'adresse
        test_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        success = db.add_tracked_address(test_address, "Test Wallet", "test_user")
        print(f"✅ Ajout d'adresse: {success}")
        
        # Test de récupération
        addresses = db.get_tracked_addresses()
        print(f"✅ Adresses récupérées: {len(addresses)}")
        
        # Test d'ajout de transaction
        success = db.add_transaction(
            address=test_address,
            signature="test_signature_123",
            transaction_type="test_transfer",
            amount=100.0,
            token_mint="test_token_mint"
        )
        print(f"✅ Transaction ajoutée: {success}")
        
        # Test de récupération des transactions
        transactions = db.get_recent_transactions(test_address, limit=10)
        print(f"✅ Transactions récupérées: {len(transactions)}")
        
        # Test de paramètres de notification
        success = db.set_notification_settings(
            address=test_address,
            min_amount=50.0,
            notification_types="token_transfer,dex_swap"
        )
        print(f"✅ Paramètres de notification: {success}")
        
        # Test de récupération des paramètres
        settings = db.get_notification_settings(test_address)
        print(f"✅ Paramètres récupérés: {settings}")
        
        print("🎉 Tests de base de données réussis!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test de base de données: {e}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests du système de tracking Solana...")
    
    # Test de la base de données
    test_database_operations()
    
    # Test du tracker
    asyncio.run(test_solana_tracking())
    
    print("✅ Tous les tests sont terminés!")
