#!/usr/bin/env python3
"""
Script pour exécuter le swap réel - Version avec checksum
"""

import asyncio
import httpx
from eth_account import Account
from web3 import Web3
from web3.middleware import geth_poa_middleware

async def execute_real_swap():
    """Exécute le swap réel pour le token"""
    print("🚀 EXÉCUTION DU SWAP RÉEL - VERSION CHECKSUM")
    print("=" * 60)
    
    # Configuration
    zerox_base_url = "https://api.0x.org"
    zerox_api_key = "85cbbc10-bb88-45d9-a527-c4f502a06e76"
    private_key = "0x77c59724588bdde9dc0aaaafe91902fd1d8bc6b29d51d69a06c989e091f80814"
    base_rpc_url = "https://mainnet.base.org"
    
    # Configuration Web3
    w3 = Web3(Web3.HTTPProvider(base_rpc_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # Créer le compte
    account = Account.from_key(private_key)
    wallet_address = account.address
    
    # Paramètres du swap
    token_address = "0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69"
    eth_amount = 0.0001
    eth_amount_wei = str(int(eth_amount * 10**18))
    chain_id = 8453  # Base
    
    print(f"📍 Adresse du wallet: {wallet_address}")
    print(f"🎯 Token à acheter: {token_address}")
    print(f"💰 Montant ETH: {eth_amount} ETH")
    print(f"⛓️  Chain ID: {chain_id}")
    
    # Vérifier la balance ETH
    try:
        eth_balance = w3.eth.get_balance(wallet_address)
        eth_balance_eth = w3.from_wei(eth_balance, 'ether')
        print(f"💳 Balance ETH actuelle: {eth_balance_eth:.6f} ETH")
        
        if eth_balance < int(eth_amount_wei):
            print(f"❌ Balance insuffisante ! Requis: {eth_amount} ETH, Disponible: {eth_balance_eth:.6f} ETH")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la balance: {e}")
        return False
    
    # Obtenir le quote
    print(f"\n🔄 Obtention du quote...")
    headers = {
        "0x-api-key": zerox_api_key,
        "0x-version": "v2",
        "Content-Type": "application/json"
    }
    
    quote_params = {
        "chainId": chain_id,
        "sellToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # ETH natif
        "buyToken": token_address,
        "sellAmount": eth_amount_wei,
        "taker": wallet_address,
        "slippageBps": "10000"  # 100% slippage
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{zerox_base_url}/swap/allowance-holder/quote",
                headers=headers,
                params=quote_params,
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"❌ Erreur lors de l'obtention du quote: {response.status_code}")
                print(f"📝 Réponse: {response.text}")
                return False
            
            quote_data = response.json()
            print("✅ Quote obtenu avec succès !")
            
            # Vérifier la liquidité
            if not quote_data.get('liquidityAvailable', False):
                print("❌ Pas de liquidité disponible")
                return False
            
            # Récupérer les données de transaction
            transaction_data = quote_data.get('transaction')
            if not transaction_data:
                print("❌ Pas de données de transaction dans le quote")
                return False
            
            print(f"📋 Détails de la transaction:")
            print(f"   📍 To: {transaction_data.get('to')}")
            print(f"   ⛽ Gas: {transaction_data.get('gas')}")
            print(f"   💸 Value: {transaction_data.get('value')} wei")
            print(f"   🎯 Tokens à recevoir: {quote_data.get('buyAmount')}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention du quote: {e}")
        return False
    
    # Construire et signer la transaction
    print(f"\n🔐 Construction de la transaction...")
    
    try:
        # Obtenir le nonce
        nonce = w3.eth.get_transaction_count(wallet_address)
        
        # Convertir l'adresse en checksum
        to_address_raw = transaction_data.get('to')
        to_address = w3.to_checksum_address(to_address_raw)
        print(f"📍 Adresse 'to' convertie en checksum: {to_address}")
        
        # Vérifier que l'adresse est un contrat valide
        try:
            code = w3.eth.get_code(to_address)
            if not code or code == b'':
                print(f"❌ L'adresse {to_address} n'est pas un contrat valide")
                return False
            print(f"✅ Contrat valide détecté à l'adresse {to_address}")
        except Exception as e:
            print(f"⚠️  Impossible de vérifier le contrat: {e}")
        
        # Construire la transaction avec validation
        transaction = {
            'to': to_address,
            'data': transaction_data.get('data', '0x'),
            'value': int(transaction_data.get('value', 0)),
            'gas': int(transaction_data.get('gas', 300000)),
            'gasPrice': int(transaction_data.get('gasPrice', w3.eth.gas_price)),
            'nonce': nonce,
            'chainId': chain_id
        }
        
        # Validation supplémentaire
        if not transaction['data'] or transaction['data'] == '0x':
            print(f"❌ Données de transaction vides")
            return False
        
        print(f"📝 Transaction construite:")
        print(f"   📍 To: {transaction['to']}")
        print(f"   ⛽ Gas: {transaction['gas']}")
        print(f"   💸 Value: {transaction['value']} wei")
        print(f"   🔢 Nonce: {transaction['nonce']}")
        print(f"   ⛓️  Chain ID: {transaction['chainId']}")
        print(f"   📄 Data length: {len(transaction['data'])} chars")
        
        # Estimer le gas si nécessaire
        try:
            estimated_gas = w3.eth.estimate_gas(transaction)
            print(f"⛽ Gas estimé par Web3: {estimated_gas}")
            if estimated_gas > transaction['gas']:
                print(f"⚠️  Gas estimé plus élevé que celui du quote")
                transaction['gas'] = int(estimated_gas * 1.2)  # Ajouter 20% de marge
                print(f"⛽ Gas ajusté: {transaction['gas']}")
        except Exception as e:
            print(f"⚠️  Impossible d'estimer le gas: {e}")
        
        # Signer la transaction
        print(f"\n🔐 Signature de la transaction...")
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        print("✅ Transaction signée")
        
        # Envoyer la transaction
        print(f"\n📡 Envoi de la transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"🎉 TRANSACTION ENVOYÉE !")
        print(f"📝 Hash de transaction: {tx_hash_hex}")
        print(f"🔗 Explorer: https://basescan.org/tx/{tx_hash_hex}")
        
        # Attendre la confirmation
        print(f"\n⏳ Attente de la confirmation...")
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print(f"✅ TRANSACTION CONFIRMÉE !")
                print(f"📊 Block: {receipt.blockNumber}")
                print(f"⛽ Gas utilisé: {receipt.gasUsed}")
                print(f"🎯 Tokens achetés avec succès !")
                return True
            else:
                print(f"❌ Transaction échouée")
                return False
        except Exception as e:
            print(f"⚠️  Transaction envoyée mais confirmation en attente: {e}")
            print(f"📝 Hash: {tx_hash_hex}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de la transaction: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale"""
    print("🚀 SCRIPT D'EXÉCUTION DE SWAP - VERSION CHECKSUM")
    print("=" * 60)
    print("⚠️  ATTENTION: Ce script va effectuer une transaction RÉELLE sur Base !")
    print("💰 Vous allez dépenser 0.0001 ETH pour acheter des tokens")
    print("=" * 60)
    
    # Demander confirmation
    confirmation = input("\n❓ Voulez-vous continuer ? (oui/non): ").lower().strip()
    
    if confirmation not in ['oui', 'o', 'yes', 'y']:
        print("❌ Transaction annulée par l'utilisateur")
        return False
    
    success = await execute_real_swap()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SWAP EXÉCUTÉ AVEC SUCCÈS !")
        print("💡 Vous avez maintenant des tokens dans votre wallet")
    else:
        print("💥 Le swap a échoué")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
