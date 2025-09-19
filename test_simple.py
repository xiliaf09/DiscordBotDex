#!/usr/bin/env python3
"""
Test simple du bot sans importer config.py
"""

import asyncio
import httpx
from eth_account import Account

async def test_0x_integration():
    """Test simple de l'intégration 0x"""
    print("🧪 Test Simple de l'Intégration 0x")
    print("=" * 50)
    
    # Configuration
    zerox_base_url = "https://api.0x.org"
    zerox_api_key = "85cbbc10-bb88-45d9-a527-c4f502a06e76"
    private_key = "0x77c59724588bdde9dc0aaaafe91902fd1d8bc6b29d51d69a06c989e091f80814"
    
    # Calculer l'adresse du wallet
    account = Account.from_key(private_key)
    wallet_address = account.address
    
    print(f"📍 Adresse du wallet: {wallet_address}")
    print(f"🔑 Clé API 0x: {'*' * (len(zerox_api_key) - 4) + zerox_api_key[-4:]}")
    
    headers = {
        "0x-api-key": zerox_api_key,
        "0x-version": "v2",
        "Content-Type": "application/json"
    }
    
    # Test avec un token réel sur Base
    test_params = {
        "chainId": 8453,  # Base
        "sellToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # ETH natif
        "buyToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
        "sellAmount": "1000000000000000",  # 0.001 ETH
        "taker": wallet_address,
        "slippageBps": "10000"  # 100% slippage
    }
    
    print(f"\n🔄 Test de quote: 0.001 ETH -> USDC")
    print(f"📡 Endpoint: {zerox_base_url}/swap/allowance-holder/quote")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{zerox_base_url}/swap/allowance-holder/quote",
                headers=headers,
                params=test_params,
                timeout=10.0
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                quote_data = response.json()
                print("✅ Quote obtenu avec succès !")
                
                # Vérifier les données importantes
                transaction = quote_data.get('transaction', {})
                to_address = transaction.get('to', '')
                
                print(f"📍 Adresse 'to': {to_address}")
                print(f"⛽ Gas: {transaction.get('gas', 'N/A')}")
                print(f"💸 Value: {transaction.get('value', 'N/A')}")
                print(f"🎯 Buy Amount: {quote_data.get('buyAmount', 'N/A')}")
                
                # Validation de l'adresse 'to'
                if to_address.startswith('0x') and len(to_address) == 42:
                    print("✅ Adresse 'to' valide")
                else:
                    print(f"❌ Adresse 'to' invalide: {to_address}")
                    return False
                
                # Vérifier la liquidité
                if quote_data.get('liquidityAvailable', False):
                    print("✅ Liquidité disponible")
                else:
                    print("❌ Pas de liquidité")
                    return False
                
                print("\n🎉 Test réussi ! Le bot devrait maintenant fonctionner correctement.")
                return True
                
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(f"📝 Réponse: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

async def main():
    """Fonction principale"""
    success = await test_0x_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tous les tests sont passés !")
        print("💡 Votre bot Discord est maintenant prêt à être utilisé.")
        print("\n📋 Pour tester le bot:")
        print("1. Démarrez le bot Discord")
        print("2. Utilisez: !testsnipe 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 0.001")
        print("3. Remplacez l'adresse du token par celle que vous voulez sniper")
    else:
        print("💥 Le test a échoué. Vérifiez votre configuration.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
