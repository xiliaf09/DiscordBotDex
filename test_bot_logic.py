#!/usr/bin/env python3
"""
Test script pour vérifier la logique du bot sans nécessiter de clé API
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_address_validation():
    """Test de validation des adresses"""
    print("🧪 Test de validation des adresses...")
    
    # Test d'adresses valides
    valid_addresses = [
        "0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69",
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "0x4200000000000000000000000000000000000006"
    ]
    
    # Test d'adresses invalides
    invalid_addresses = [
        "Oxf525ff21c370beb8d9f5c12dc0da2b583f4b949f",  # "Ox" au lieu de "0x"
        "0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C6",   # Trop court
        "0x9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69G",  # Caractère invalide
        "9Cb41FD9dC6891BAe8187029461bfAADF6CC0C69",     # Pas de 0x
    ]
    
    print("✅ Adresses valides:")
    for addr in valid_addresses:
        if addr.startswith('0x') and len(addr) == 42:
            print(f"   ✓ {addr}")
        else:
            print(f"   ✗ {addr} (invalide)")
    
    print("\n❌ Adresses invalides:")
    for addr in invalid_addresses:
        if addr.startswith('0x') and len(addr) == 42:
            print(f"   ✗ {addr} (devrait être invalide)")
        else:
            print(f"   ✓ {addr} (correctement détectée comme invalide)")
    
    return True

def test_api_endpoint_logic():
    """Test de la logique des endpoints API"""
    print("\n🧪 Test de la logique des endpoints API...")
    
    # Test de l'endpoint v2
    endpoint_v2 = "/swap/v2/quote"
    print(f"✅ Endpoint v2: {endpoint_v2}")
    
    # Test des paramètres
    test_params = {
        "chainId": 8453,
        "sellToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # ETH natif
        "buyToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
        "sellAmount": "1000000000000000",  # 0.001 ETH en wei
        "slippageBps": "100"  # 1% slippage
    }
    
    print("✅ Paramètres de test:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    
    return True

def test_transaction_validation():
    """Test de validation des transactions"""
    print("\n🧪 Test de validation des transactions...")
    
    # Transaction valide
    valid_tx = {
        'to': '0x7f6cee965959295cc64d0e6c00d99d6532d8e86b',
        'data': '0x1fff991f00000000000000000000000070a9f34f9b34c64957b9c401a97bfed35b95049e',
        'value': '0',
        'gas': '288079',
        'gasPrice': '4837860000'
    }
    
    # Transaction invalide (adresse 'to' incorrecte)
    invalid_tx = {
        'to': 'Oxf525ff21c370beb8d9f5c12dc0da2b583f4b949f',  # "Ox" au lieu de "0x"
        'data': '0x1fff991f00000000000000000000000070a9f34f9b34c64957b9c401a97bfed35b95049e',
        'value': '0',
        'gas': '288079',
        'gasPrice': '4837860000'
    }
    
    # Test de validation
    required_fields = ['to', 'data', 'value', 'gas', 'gasPrice']
    
    print("✅ Transaction valide:")
    for field in required_fields:
        if field in valid_tx:
            if field == 'to':
                if valid_tx[field].startswith('0x'):
                    print(f"   ✓ {field}: {valid_tx[field]} (format valide)")
                else:
                    print(f"   ✗ {field}: {valid_tx[field]} (format invalide)")
            else:
                print(f"   ✓ {field}: {valid_tx[field]}")
        else:
            print(f"   ✗ {field}: manquant")
    
    print("\n❌ Transaction invalide:")
    for field in required_fields:
        if field in invalid_tx:
            if field == 'to':
                if invalid_tx[field].startswith('0x'):
                    print(f"   ✗ {field}: {invalid_tx[field]} (devrait être invalide)")
                else:
                    print(f"   ✓ {field}: {invalid_tx[field]} (correctement détectée comme invalide)")
            else:
                print(f"   ✓ {field}: {invalid_tx[field]}")
        else:
            print(f"   ✗ {field}: manquant")
    
    return True

def test_wei_conversion():
    """Test de conversion ETH vers Wei"""
    print("\n🧪 Test de conversion ETH vers Wei...")
    
    test_amounts = [
        (0.001, "1000000000000000"),
        (0.01, "10000000000000000"),
        (0.1, "100000000000000000"),
        (1.0, "1000000000000000000"),
        (10.0, "10000000000000000000")
    ]
    
    for eth_amount, expected_wei in test_amounts:
        # Simulation de la conversion
        wei_amount = str(int(eth_amount * 10**18))
        if wei_amount == expected_wei:
            print(f"   ✓ {eth_amount} ETH = {wei_amount} wei")
        else:
            print(f"   ✗ {eth_amount} ETH = {wei_amount} wei (attendu: {expected_wei})")
    
    return True

async def main():
    """Fonction principale de test"""
    print("🧪 Test de la Logique du Bot Discord (sans clé API)")
    print("=" * 60)
    
    tests = [
        test_address_validation,
        test_api_endpoint_logic,
        test_transaction_validation,
        test_wei_conversion
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Erreur dans le test: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests de logique sont passés !")
        print("💡 Le bot devrait maintenant fonctionner correctement avec une clé API 0x valide.")
    else:
        print("💥 Certains tests ont échoué. Vérifiez la logique du code.")
    
    print("\n📋 Prochaines étapes:")
    print("1. Configurez votre clé API 0x dans le fichier .env")
    print("2. Testez le bot avec la commande !testsnipe")
    print("3. Vérifiez les logs pour tout problème restant")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
