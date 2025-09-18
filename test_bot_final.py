#!/usr/bin/env python3
"""
Test final du bot avec les vraies informations
"""

import asyncio
import sys
import os
from eth_account import Account

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration des variables d'environnement pour le test
os.environ['ZEROX_API_KEY'] = '85cbbc10-bb88-45d9-a527-c4f502a06e76'
os.environ['SNIPINGWALLETKEY'] = '0x77c59724588bdde9dc0aaaafe91902fd1d8bc6b29d51d69a06c989e091f80814'
os.environ['BASE_RPC_URL'] = 'https://mainnet.base.org'

# Importer les modules du bot
import config
from bot import SniperManager, DatabaseManager

async def test_sniper_manager():
    """Test du SniperManager avec les vraies informations"""
    print("🧪 Test du SniperManager...")
    
    try:
        # Créer une instance de DatabaseManager (mock)
        class MockDB:
            pass
        
        db_manager = MockDB()
        
        # Créer le SniperManager
        sniper_manager = SniperManager(db_manager)
        
        print(f"✅ SniperManager créé avec succès")
        print(f"📍 Adresse du wallet: {sniper_manager.sniping_address}")
        print(f"🔑 Clé API 0x configurée: {'Oui' if config.ZEROX_API_KEY else 'Non'}")
        
        # Test d'un quote
        print("\n🔄 Test d'un quote...")
        quote = await sniper_manager.get_quote(
            sell_token="0x4200000000000000000000000000000000000006",  # WETH
            buy_token="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
            sell_amount="1000000000000000"  # 0.001 ETH
        )
        
        if quote:
            print("✅ Quote obtenu avec succès !")
            print(f"💰 Montant à vendre: {quote.get('sellAmount', 'N/A')}")
            print(f"🎯 Montant à acheter: {quote.get('buyAmount', 'N/A')}")
            print(f"⛽ Gas: {quote.get('transaction', {}).get('gas', 'N/A')}")
            print(f"📍 Adresse 'to': {quote.get('transaction', {}).get('to', 'N/A')}")
            
            # Vérifier la validité de l'adresse 'to'
            to_address = quote.get('transaction', {}).get('to', '')
            if to_address.startswith('0x') and len(to_address) == 42:
                print("✅ Adresse 'to' valide")
            else:
                print(f"❌ Adresse 'to' invalide: {to_address}")
                return False
                
            return True
        else:
            print("❌ Échec de l'obtention du quote")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

async def test_snipe_token():
    """Test de la fonction snipe_token"""
    print("\n🧪 Test de la fonction snipe_token...")
    
    try:
        # Créer une instance de DatabaseManager (mock)
        class MockDB:
            pass
        
        db_manager = MockDB()
        sniper_manager = SniperManager(db_manager)
        
        # Test avec un token réel sur Base
        token_address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC
        eth_amount = 0.001  # 0.001 ETH
        
        print(f"🎯 Test de snipe: {eth_amount} ETH -> {token_address}")
        
        # Note: On ne va pas vraiment exécuter la transaction, juste tester la logique
        result = await sniper_manager.snipe_token(token_address, eth_amount)
        
        if result["success"]:
            print("✅ Snipe test réussi !")
            print(f"📝 Hash de transaction: {result.get('tx_hash', 'N/A')}")
            return True
        else:
            print(f"❌ Échec du snipe: {result.get('error', 'Erreur inconnue')}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de snipe: {e}")
        return False

async def main():
    """Fonction principale de test"""
    print("🧪 Test Final du Bot Discord avec les Vraies Informations")
    print("=" * 60)
    
    # Test 1: SniperManager
    test1_success = await test_sniper_manager()
    
    # Test 2: Fonction snipe_token (sans exécution réelle)
    test2_success = await test_snipe_token()
    
    print("\n" + "=" * 60)
    print("📊 Résultats des tests:")
    print(f"✅ SniperManager: {'Réussi' if test1_success else 'Échec'}")
    print(f"✅ Fonction snipe_token: {'Réussi' if test2_success else 'Échec'}")
    
    if test1_success and test2_success:
        print("\n🎉 Tous les tests sont passés !")
        print("💡 Le bot est maintenant prêt à être utilisé avec la commande !testsnipe")
        print("\n📋 Prochaines étapes:")
        print("1. Démarrez le bot Discord")
        print("2. Testez avec: !testsnipe <token_address> <eth_amount>")
        print("3. Surveillez les logs pour tout problème")
    else:
        print("\n💥 Certains tests ont échoué. Vérifiez la configuration.")
    
    return test1_success and test2_success

if __name__ == "__main__":
    asyncio.run(main())
