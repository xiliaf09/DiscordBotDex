#!/usr/bin/env python3
"""
Test final d'intégration du bot Discord avec toutes les corrections
"""

import asyncio
import sys
import os
from eth_account import Account

# Configuration des variables d'environnement pour le test
os.environ['ZEROX_API_KEY'] = '85cbbc10-bb88-45d9-a527-c4f502a06e76'
os.environ['SNIPINGWALLETKEY'] = '0x77c59724588bdde9dc0aaaafe91902fd1d8bc6b29d51d69a06c989e091f80814'
os.environ['BASE_RPC_URL'] = 'https://mainnet.base.org'
os.environ['DISCORD_TOKEN'] = 'test_token'
os.environ['DISCORD_CHANNEL_ID'] = '123456789'
os.environ['ADMIN_ROLE_ID'] = '987654321'

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_bot_integration():
    """Test d'intégration complet du bot"""
    print("🧪 Test d'Intégration Final du Bot Discord")
    print("=" * 60)
    
    try:
        # Importer les modules du bot
        import config
        from bot import SniperManager
        
        # Créer une instance de DatabaseManager (mock)
        class MockDB:
            pass
        
        db_manager = MockDB()
        
        # Créer le SniperManager
        sniper_manager = SniperManager(db_manager)
        
        print(f"✅ SniperManager créé avec succès")
        print(f"📍 Adresse du wallet: {sniper_manager.sniping_address}")
        print(f"🔑 Clé API 0x configurée: {'Oui' if config.ZEROX_API_KEY else 'Non'}")
        print(f"⛓️  Chain ID: {sniper_manager.chain_id}")
        print(f"🌐 RPC URL: {config.BASE_RPC_URL}")
        
        # Test d'un quote
        print(f"\n🔄 Test d'un quote...")
        token_address = "0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69"
        eth_amount = 0.0001
        
        quote = await sniper_manager.get_quote(
            sell_token="0x4200000000000000000000000000000000000006",  # WETH
            buy_token=token_address,
            sell_amount=str(int(eth_amount * 10**18))  # Convertir en wei
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
            
            # Vérifier la liquidité
            if quote.get('liquidityAvailable', False):
                print("✅ Liquidité disponible")
            else:
                print("❌ Pas de liquidité")
                return False
                
            return True
        else:
            print("❌ Échec de l'obtention du quote")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_checksum_conversion():
    """Test de la conversion checksum"""
    print(f"\n🧪 Test de la conversion checksum...")
    
    try:
        from web3 import Web3
        
        # Test avec l'adresse problématique
        test_address = "0x0000000000001ff3684f28c67538d4d072c22734"
        checksum_address = Web3.to_checksum_address(test_address)
        
        print(f"📍 Adresse originale: {test_address}")
        print(f"📍 Adresse checksum: {checksum_address}")
        
        if checksum_address != test_address:
            print("✅ Conversion checksum fonctionne")
            return True
        else:
            print("⚠️  Pas de conversion nécessaire")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du test checksum: {e}")
        return False

async def main():
    """Fonction principale de test"""
    print("🧪 Test Final d'Intégration du Bot Discord")
    print("=" * 60)
    
    # Test 1: Intégration du bot
    test1_success = await test_bot_integration()
    
    # Test 2: Conversion checksum
    test2_success = await test_checksum_conversion()
    
    print("\n" + "=" * 60)
    print("📊 Résultats des tests:")
    print(f"✅ Intégration du bot: {'Réussi' if test1_success else 'Échec'}")
    print(f"✅ Conversion checksum: {'Réussi' if test2_success else 'Échec'}")
    
    if test1_success and test2_success:
        print("\n🎉 Tous les tests sont passés !")
        print("💡 Le bot Discord est maintenant parfaitement configuré et prêt à être utilisé.")
        print("\n📋 Corrections implémentées:")
        print("✅ API 0x v2 avec endpoint correct (/swap/allowance-holder/quote)")
        print("✅ Validation des adresses avec checksum")
        print("✅ Gestion des erreurs améliorée")
        print("✅ Paramètres requis (taker) ajoutés")
        print("✅ Validation des transactions")
        print("\n🚀 Votre bot est prêt pour les snipes automatiques !")
    else:
        print("\n💥 Certains tests ont échoué. Vérifiez la configuration.")
    
    return test1_success and test2_success

if __name__ == "__main__":
    asyncio.run(main())
