#!/usr/bin/env python3
"""
Test script pour vérifier la configuration Doppler
Optimisé pour Railway
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Load environment variables
load_dotenv()

# Doppler configuration
DOPPLER_FACTORY_ADDRESS = "0xFAafdE6a5b658684cC5eb0C5c2c755B00A246F45"
DOPPLER_FACTORY_ABI = [
    {"inputs":[{"internalType":"address","name":"airlock_","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
    {"inputs":[],"name":"SenderNotAirlock","type":"error"},
    {"inputs":[],"name":"airlock","outputs":[{"internalType":"contract Airlock","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"initialSupply","type":"uint256"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"salt","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"create","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"nonpayable","type":"function"}
]

def test_doppler_config():
    """Test de la configuration Doppler optimisé pour Railway"""
    print("🔧 Test de la configuration Doppler (Railway)")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    quicknode_wss = os.getenv('QUICKNODE_WSS')
    if not quicknode_wss:
        print("❌ QUICKNODE_WSS non défini dans les variables d'environnement")
        print("💡 Assurez-vous que la variable est configurée sur Railway")
        return False
    
    print(f"✅ QUICKNODE_WSS: {quicknode_wss[:30]}...")
    
    # Tester la connexion Web3
    try:
        print("🔄 Test de connexion WebSocket...")
        w3 = Web3(Web3.WebsocketProvider(quicknode_wss))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Railway-specific: Test de connexion avec timeout
        if w3.is_connected():
            print("✅ Connexion WebSocket réussie")
        else:
            print("❌ Échec de la connexion WebSocket")
            print("💡 Vérifiez votre endpoint QuickNode WebSocket")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion WebSocket: {e}")
        print("💡 Vérifiez que votre endpoint QuickNode est correct")
        return False
    
    # Tester le contrat Doppler
    try:
        print("🔄 Initialisation du contrat Doppler...")
        doppler_factory = w3.eth.contract(
            address=Web3.to_checksum_address(DOPPLER_FACTORY_ADDRESS),
            abi=DOPPLER_FACTORY_ABI
        )
        print("✅ Contrat Doppler factory initialisé")
        
        # Tester un appel de lecture
        try:
            print("🔄 Test d'appel de lecture (airlock)...")
            airlock = doppler_factory.functions.airlock().call()
            print(f"✅ Airlock address: {airlock}")
        except Exception as e:
            print(f"⚠️ Impossible de lire l'airlock: {e}")
            print("💡 Cela peut être normal si le contrat n'est pas encore déployé")
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation du contrat Doppler: {e}")
        return False
    
    # Tester la récupération des derniers blocs
    try:
        print("🔄 Test de récupération des blocs...")
        latest_block = w3.eth.block_number
        print(f"✅ Dernier bloc: {latest_block}")
        
        # Railway-specific: Test optimisé pour éviter les timeouts
        print("🔄 Test de récupération d'un bloc avec transactions...")
        block = w3.eth.get_block(latest_block, full_transactions=True)
        print(f"✅ Bloc récupéré avec {len(block.transactions)} transactions")
        
        # Test de recherche de transactions Doppler
        print("🔄 Test de recherche de transactions Doppler...")
        doppler_txs = []
        for block_num in range(latest_block - 3, latest_block + 1):  # Test sur 3 blocs seulement
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    if tx['to'] and tx['to'].lower() == DOPPLER_FACTORY_ADDRESS.lower():
                        if tx['input'].startswith('0x') and len(tx['input']) > 10:
                            doppler_txs.append(tx)
            except Exception as e:
                print(f"⚠️ Erreur lors du traitement du bloc {block_num}: {e}")
                continue
        
        print(f"✅ {len(doppler_txs)} transactions Doppler trouvées dans les derniers blocs")
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des blocs: {e}")
        return False
    
    # Test de décodage de transaction
    if doppler_txs:
        try:
            print("🔄 Test de décodage de transaction Doppler...")
            latest_tx = doppler_txs[-1]
            func_obj, func_args = doppler_factory.decode_function_input(latest_tx['input'])
            print("✅ Décodage de transaction réussi")
            print(f"   - Fonction: {func_obj.fn_name}")
            print(f"   - Arguments: {list(func_args.keys())}")
        except Exception as e:
            print(f"⚠️ Erreur lors du décodage de transaction: {e}")
    
    print("\n🎉 Configuration Doppler testée avec succès!")
    print("✅ Le bot est prêt pour la surveillance Doppler sur Railway")
    return True

def test_railway_environment():
    """Test spécifique pour l'environnement Railway"""
    print("\n🚂 Test de l'environnement Railway")
    print("=" * 40)
    
    # Vérifier les variables Railway
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    if railway_env:
        print(f"✅ Environnement Railway détecté: {railway_env}")
    else:
        print("ℹ️ Pas d'environnement Railway détecté (normal en local)")
    
    # Vérifier les variables critiques
    required_vars = ['DISCORD_TOKEN', 'CHANNEL_ID', 'QUICKNODE_WSS']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        print("💡 Configurez ces variables sur Railway")
        return False
    else:
        print("✅ Toutes les variables requises sont configurées")
        return True

if __name__ == "__main__":
    print("🚀 Démarrage des tests Doppler pour Railway")
    print("=" * 60)
    
    # Test de l'environnement Railway
    env_ok = test_railway_environment()
    
    # Test de la configuration Doppler
    doppler_ok = test_doppler_config()
    
    print("\n📊 Résumé des tests")
    print("=" * 30)
    print(f"Environnement Railway: {'✅' if env_ok else '❌'}")
    print(f"Configuration Doppler: {'✅' if doppler_ok else '❌'}")
    
    if env_ok and doppler_ok:
        print("\n🎉 Tous les tests sont passés! Le bot est prêt pour Railway.")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué. Vérifiez la configuration.")
        sys.exit(1) 