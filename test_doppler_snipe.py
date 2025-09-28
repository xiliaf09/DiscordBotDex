#!/usr/bin/env python3
"""
Script de test pour le système de sniping Doppler $DAU
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration de test
TEST_WEBHOOK_URL = "http://localhost:3000/webhook/snipe"
TEST_TOKEN_ADDRESS = "0x1234567890123456789012345678901234567890"  # Adresse de test

async def test_webhook_health():
    """Test de santé du serveur webhook"""
    print("🔍 Test de santé du webhook...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TEST_WEBHOOK_URL.replace('/webhook/snipe', '/health')) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Serveur webhook OK")
                    print(f"   Wallet: {data.get('wallet', 'N/A')}")
                    print(f"   Chain: {data.get('chain', 'N/A')}")
                    return True
                else:
                    print(f"❌ Erreur serveur: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

async def test_webhook_balance():
    """Test du solde ETH"""
    print("\n💰 Test du solde ETH...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TEST_WEBHOOK_URL.replace('/webhook/snipe', '/balance/eth')) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        balance = data.get('balance', 'N/A')
                        print(f"✅ Solde ETH: {balance}")
                        return True
                    else:
                        print(f"❌ Erreur: {data.get('error', 'Unknown')}")
                        return False
                else:
                    print(f"❌ Erreur serveur: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

async def test_webhook_snipe():
    """Test du webhook de snipe"""
    print("\n🎯 Test du webhook de snipe...")
    
    # Données de test
    test_data = {
        "action": "snipe",
        "token_address": TEST_TOKEN_ADDRESS,
        "amount_eth": 0.01,  # Petit montant pour le test
        "platform": "doppler",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TEST_WEBHOOK_URL,
                json=test_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print(f"✅ Webhook snipe OK")
                        print(f"   Hash: {data.get('transactionHash', 'N/A')}")
                        return True
                    else:
                        print(f"❌ Échec snipe: {data.get('error', 'Unknown')}")
                        return False
                else:
                    print(f"❌ Erreur serveur: {response.status}")
                    try:
                        error_data = await response.json()
                        print(f"   Détail: {error_data}")
                    except:
                        pass
                    return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

async def test_discord_bot_config():
    """Test de la configuration du bot Discord"""
    print("\n🤖 Test de la configuration Discord...")
    
    # Variables d'environnement requises
    required_vars = [
        'DOPPLER_SNIPE_ENABLED',
        'DOPPLER_SNIPE_TICKER', 
        'DOPPLER_SNIPE_AMOUNT',
        'TELEGRAM_WEBHOOK_URL',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Configuration Discord OK")
        return True

def print_configuration_guide():
    """Affiche le guide de configuration"""
    print("\n" + "="*60)
    print("📋 GUIDE DE CONFIGURATION")
    print("="*60)
    
    print("\n1. Variables d'environnement Discord (.env):")
    print("""
DOPPLER_SNIPE_ENABLED=true
DOPPLER_SNIPE_TICKER=DAU
DOPPLER_SNIPE_AMOUNT=0.1
TELEGRAM_WEBHOOK_URL=http://localhost:3000/webhook/snipe
TELEGRAM_CHAT_ID=votre_chat_id
    """)
    
    print("\n2. Démarrage du serveur webhook:")
    print("""
cd tgbotv4-master
npm install express
npm run webhook
    """)
    
    print("\n3. Commandes Discord:")
    print("""
!snipedau 0.1    # Active le sniper avec 0.1 ETH
!snipedauconfig  # Voir la configuration
!snipedauoff     # Désactive le sniper
    """)
    
    print("\n4. Test du système:")
    print("""
python test_doppler_snipe.py
    """)

async def main():
    """Fonction principale de test"""
    print("🎯 TEST DU SYSTÈME DE SNIPING DOPPLER $DAU")
    print("="*50)
    
    # Tests
    tests = [
        ("Configuration Discord", test_discord_bot_config),
        ("Santé Webhook", test_webhook_health),
        ("Solde ETH", test_webhook_balance),
        ("Webhook Snipe", test_webhook_snipe)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés! Le système est prêt.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        print_configuration_guide()

if __name__ == "__main__":
    asyncio.run(main()) 