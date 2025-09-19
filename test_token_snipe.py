#!/usr/bin/env python3
"""
Test de snipe pour le token spécifique demandé
"""

import asyncio
import httpx
from eth_account import Account

async def test_token_snipe():
    """Test de snipe pour le token 0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69"""
    print("🎯 Test de Snipe - Token Spécifique")
    print("=" * 60)
    
    # Configuration
    zerox_base_url = "https://api.0x.org"
    zerox_api_key = "85cbbc10-bb88-45d9-a527-c4f502a06e76"
    private_key = "0x77c59724588bdde9dc0aaaafe91902fd1d8bc6b29d51d69a06c989e091f80814"
    
    # Calculer l'adresse du wallet
    account = Account.from_key(private_key)
    wallet_address = account.address
    
    # Paramètres du test
    token_address = "0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69"
    eth_amount = 0.0001
    eth_amount_wei = str(int(eth_amount * 10**18))  # Convertir en wei
    
    print(f"📍 Adresse du wallet: {wallet_address}")
    print(f"🎯 Token à acheter: {token_address}")
    print(f"💰 Montant ETH: {eth_amount} ETH ({eth_amount_wei} wei)")
    print(f"🔑 Clé API 0x: {'*' * (len(zerox_api_key) - 4) + zerox_api_key[-4:]}")
    
    headers = {
        "0x-api-key": zerox_api_key,
        "0x-version": "v2",
        "Content-Type": "application/json"
    }
    
    # Paramètres pour le quote
    test_params = {
        "chainId": 8453,  # Base
        "sellToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # ETH natif
        "buyToken": token_address,  # Token à acheter
        "sellAmount": eth_amount_wei,  # Montant en wei
        "taker": wallet_address,
        "slippageBps": "10000"  # 100% slippage
    }
    
    print(f"\n🔄 Test de quote: {eth_amount} ETH -> {token_address}")
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
                
                # Analyser les données du quote
                transaction = quote_data.get('transaction', {})
                to_address = transaction.get('to', '')
                
                print(f"\n📋 Détails du Quote:")
                print(f"📍 Adresse 'to': {to_address}")
                print(f"⛽ Gas: {transaction.get('gas', 'N/A')}")
                print(f"💸 Value: {transaction.get('value', 'N/A')} wei")
                print(f"🎯 Montant à acheter: {quote_data.get('buyAmount', 'N/A')} tokens")
                print(f"💰 Montant à vendre: {quote_data.get('sellAmount', 'N/A')} wei")
                
                # Vérifier la liquidité
                liquidity_available = quote_data.get('liquidityAvailable', False)
                print(f"💧 Liquidité disponible: {'Oui' if liquidity_available else 'Non'}")
                
                # Vérifier les issues
                issues = quote_data.get('issues', {})
                if issues:
                    print(f"\n⚠️  Issues détectées:")
                    for key, value in issues.items():
                        if value is not None:
                            print(f"   - {key}: {value}")
                else:
                    print(f"\n✅ Aucun issue détecté")
                
                # Validation de l'adresse 'to'
                if to_address.startswith('0x') and len(to_address) == 42:
                    print(f"\n✅ Adresse 'to' valide")
                else:
                    print(f"\n❌ Adresse 'to' invalide: {to_address}")
                    return False
                
                # Vérifier si on peut exécuter la transaction
                if liquidity_available and not issues.get('simulationIncomplete', False):
                    print(f"\n🎉 Le snipe est possible !")
                    print(f"💡 Vous pouvez maintenant utiliser la commande:")
                    print(f"   !testsnipe {token_address} {eth_amount}")
                    return True
                else:
                    print(f"\n⚠️  Le snipe pourrait échouer:")
                    if not liquidity_available:
                        print(f"   - Pas de liquidité suffisante")
                    if issues.get('simulationIncomplete', False):
                        print(f"   - Simulation incomplète")
                    return False
                
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(f"📝 Réponse: {response.text}")
                
                # Analyser l'erreur
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_name = error_data.get('name', 'Unknown')
                        error_message = error_data.get('message', 'Unknown error')
                        print(f"🔍 Erreur détaillée: {error_name} - {error_message}")
                        
                        if error_name == "TOKEN_NOT_SUPPORTED":
                            print(f"💡 Ce token n'est pas supporté par l'API 0x")
                        elif error_name == "INPUT_INVALID":
                            print(f"💡 Paramètres d'entrée invalides")
                        elif error_name == "SWAP_VALIDATION_FAILED":
                            print(f"💡 Échec de validation du swap")
                    except:
                        pass
                
                return False
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

async def main():
    """Fonction principale"""
    success = await test_token_snipe()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test réussi ! Le snipe de ce token est possible.")
        print("💡 Vous pouvez maintenant utiliser votre bot Discord avec:")
        print("   !testsnipe 0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69 0.0001")
    else:
        print("💥 Le test a échoué. Ce token pourrait ne pas être échangeable.")
        print("💡 Vérifiez que:")
        print("   - Le token existe sur Base")
        print("   - Il y a de la liquidité disponible")
        print("   - Le token est supporté par l'API 0x")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
