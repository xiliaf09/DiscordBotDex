#!/usr/bin/env python3
"""
Script de test pour l'intégration Twilio avec les alertes Solana
"""

import asyncio
import logging
import config
from bot import make_solana_emergency_call

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_solana_twilio_integration():
    """Test de l'intégration Twilio pour les alertes Solana"""
    
    logger.info("🧪 Test de l'intégration Solana + Twilio")
    
    # Vérifier la configuration Twilio
    if not config.TWILIO_ACCOUNT_SID or not config.TWILIO_AUTH_TOKEN:
        logger.error("❌ Configuration Twilio manquante")
        logger.error("   Vérifiez TWILIO_ACCOUNT_SID et TWILIO_AUTH_TOKEN")
        return False
    
    if not config.TWILIO_PHONE_NUMBER or not config.YOUR_PHONE_NUMBER:
        logger.error("❌ Numéros de téléphone Twilio manquants")
        logger.error("   Vérifiez TWILIO_PHONE_NUMBER et YOUR_PHONE_NUMBER")
        return False
    
    # Vérifier la configuration Solana
    if not config.SOLANA_CALL_ENABLED:
        logger.warning("⚠️ Appels Solana désactivés (SOLANA_CALL_ENABLED=false)")
        logger.info("   Pour activer: SOLANA_CALL_ENABLED=true")
    
    logger.info(f"📱 Configuration Solana:")
    logger.info(f"   SOLANA_CALL_ENABLED: {config.SOLANA_CALL_ENABLED}")
    logger.info(f"   SOLANA_CALL_MIN_AMOUNT: {config.SOLANA_CALL_MIN_AMOUNT}")
    
    # Test de la fonction make_solana_emergency_call
    try:
        logger.info("📞 Test de l'appel d'urgence Solana...")
        
        # Données de test
        test_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        test_tx_type = "token_transfer"
        test_amount = "5.5 SOL"
        
        await make_solana_emergency_call(test_address, test_tx_type, test_amount)
        
        logger.info("✅ Test d'appel Solana réussi")
        logger.info("   Vous devriez recevoir un appel téléphonique dans quelques secondes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test d'appel Solana: {e}")
        return False

async def test_configuration_parsing():
    """Test du parsing des montants pour les seuils"""
    
    logger.info("🔍 Test du parsing des montants")
    
    test_amounts = [
        "1.5 SOL",
        "100 USDC", 
        "0.05",
        "1000",
        "2,500.75",
        "Invalid amount"
    ]
    
    for amount_str in test_amounts:
        try:
            # Simulation du parsing utilisé dans send_solana_notification
            amount_clean = str(amount_str).replace(',', '').upper()
            numeric_amount = float(''.join(filter(lambda x: x.isdigit() or x == '.', amount_clean)))
            
            logger.info(f"   '{amount_str}' -> {numeric_amount}")
            
        except (ValueError, TypeError):
            logger.info(f"   '{amount_str}' -> Erreur de parsing (ignoré)")
    
    logger.info("✅ Test de parsing terminé")

async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Démarrage des tests d'intégration Solana + Twilio")
    logger.info("=" * 60)
    
    # Test 1: Parsing des montants
    await test_configuration_parsing()
    logger.info("")
    
    # Test 2: Configuration
    logger.info("⚙️ Vérification de la configuration...")
    logger.info(f"   TWILIO_ACCOUNT_SID: {'✅ Configuré' if config.TWILIO_ACCOUNT_SID else '❌ Manquant'}")
    logger.info(f"   TWILIO_AUTH_TOKEN: {'✅ Configuré' if config.TWILIO_AUTH_TOKEN else '❌ Manquant'}")
    logger.info(f"   TWILIO_PHONE_NUMBER: {'✅ Configuré' if config.TWILIO_PHONE_NUMBER else '❌ Manquant'}")
    logger.info(f"   YOUR_PHONE_NUMBER: {'✅ Configuré' if config.YOUR_PHONE_NUMBER else '❌ Manquant'}")
    logger.info("")
    
    # Test 3: Appel réel (seulement si demandé)
    response = input("📞 Voulez-vous tester un appel téléphonique réel ? (y/N): ")
    if response.lower() in ['y', 'yes', 'oui']:
        success = await test_solana_twilio_integration()
        if success:
            logger.info("🎉 Test d'intégration réussi !")
        else:
            logger.error("💥 Test d'intégration échoué !")
    else:
        logger.info("⏭️ Test d'appel téléphonique ignoré")
    
    logger.info("=" * 60)
    logger.info("✅ Tests terminés")

if __name__ == "__main__":
    asyncio.run(main())
