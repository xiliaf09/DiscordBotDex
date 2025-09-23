#!/usr/bin/env python3
"""
Test script pour vérifier l'extraction des frais anti-sniper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web3 import Web3
import json

# Configuration de test
QUICKNODE_WSS = "wss://base-mainnet.g.alchemy.com/v2/your-key-here"  # Remplacez par votre clé
TEST_TX_HASH = "0xcf3ba3d4c42475fd7c977eee85928d37dd44f7471d7f966bcab3953a0755e83d"

def test_extract_anti_sniper_fees():
    """Test de la fonction d'extraction des frais anti-sniper"""
    try:
        # Initialiser Web3
        w3 = Web3(Web3.WebsocketProvider(QUICKNODE_WSS))
        
        if not w3.is_connected():
            print("❌ Impossible de se connecter à Web3")
            return False
        
        print("✅ Connexion Web3 réussie")
        
        # ABI pour l'événement FeeConfigSet
        fee_config_abi = {
            "anonymous": False,
            "inputs": [
                {"indexed": False, "internalType": "bytes32", "name": "poolId", "type": "bytes32"},
                {"indexed": False, "internalType": "uint24", "name": "startingFee", "type": "uint24"},
                {"indexed": False, "internalType": "uint24", "name": "endingFee", "type": "uint24"},
                {"indexed": False, "internalType": "uint256", "name": "secondsToDecay", "type": "uint256"}
            ],
            "name": "FeeConfigSet",
            "type": "event"
        }
        
        # Créer l'instance du contrat
        fee_contract = w3.eth.contract(abi=[fee_config_abi])
        
        # Récupérer la transaction
        receipt = w3.eth.get_transaction_receipt(TEST_TX_HASH)
        print(f"✅ Transaction récupérée: {len(receipt.logs)} logs trouvés")
        
        # Traiter les logs
        fee_data = None
        for log in receipt.logs:
            try:
                decoded_log = fee_contract.events.FeeConfigSet().process_log(log)
                if decoded_log:
                    starting_fee = decoded_log['args']['startingFee']
                    ending_fee = decoded_log['args']['endingFee']
                    seconds_to_decay = decoded_log['args']['secondsToDecay']
                    
                    # Calculer les pourcentages (multiplier par 1.2)
                    starting_fee_percent = (starting_fee * 1.2) / 10000
                    ending_fee_percent = (ending_fee * 1.2) / 10000
                    
                    fee_data = {
                        'starting_fee': starting_fee,
                        'ending_fee': ending_fee,
                        'seconds_to_decay': seconds_to_decay,
                        'starting_fee_percent': starting_fee_percent,
                        'ending_fee_percent': ending_fee_percent
                    }
                    
                    print("✅ Frais anti-sniper extraits avec succès:")
                    print(f"   - Starting Fee: {starting_fee} ({starting_fee_percent:.1f}%)")
                    print(f"   - Ending Fee: {ending_fee} ({ending_fee_percent:.1f}%)")
                    print(f"   - Seconds to Decay: {seconds_to_decay}")
                    
                    break
            except Exception as e:
                continue  # Skip les logs qui ne correspondent pas
        
        if fee_data:
            print("✅ Test réussi ! Les frais anti-sniper sont correctement extraits.")
            return True
        else:
            print("❌ Aucun événement FeeConfigSet trouvé dans cette transaction")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de l'extraction des frais anti-sniper...")
    print(f"📋 Transaction de test: {TEST_TX_HASH}")
    print("=" * 60)
    
    success = test_extract_anti_sniper_fees()
    
    print("=" * 60)
    if success:
        print("🎉 Test terminé avec succès !")
    else:
        print("💥 Test échoué !")
