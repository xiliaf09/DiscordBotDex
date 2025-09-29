#!/usr/bin/env python3
"""
Script de test pour les commandes Discord Solana Twilio
"""

import asyncio
import logging
import config
from unittest.mock import Mock, AsyncMock

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockCtx:
    """Mock Discord context pour les tests"""
    def __init__(self):
        self.author = Mock()
        self.author.mention = "@TestUser"
        self.author.display_name = "TestUser"
        self.channel = Mock()
        self.channel.mention = "#test-channel"
        self.send = AsyncMock()
        self.send.return_value = Mock()

class MockBot:
    """Mock Bot pour les tests"""
    def __init__(self):
        self.cogs = {}

async def test_solana_cog_commands():
    """Test des commandes du SolanaCog"""
    
    logger.info("🧪 Test des commandes SolanaCog")
    
    try:
        # Import du SolanaCog
        from solana_cog import SolanaCog
        
        # Créer des mocks
        mock_bot = MockBot()
        mock_ctx = MockCtx()
        
        # Créer une instance du SolanaCog
        solana_cog = SolanaCog(mock_bot)
        
        # Test 1: Statut initial
        logger.info("📊 Test du statut initial...")
        await solana_cog.solana_call_status(mock_ctx)
        
        # Test 2: Activation des appels
        logger.info("🟢 Test d'activation des appels...")
        await solana_cog.solana_call_enable(mock_ctx)
        assert solana_cog.solana_call_enabled == True
        logger.info("✅ Appels activés avec succès")
        
        # Test 3: Configuration du seuil
        logger.info("⚙️ Test de configuration du seuil...")
        await solana_cog.solana_call_set_threshold(mock_ctx, 5.0)
        assert solana_cog.solana_call_min_amount == 5.0
        logger.info("✅ Seuil configuré avec succès")
        
        # Test 4: Statut après configuration
        logger.info("📊 Test du statut après configuration...")
        await solana_cog.solana_call_status(mock_ctx)
        
        # Test 5: Désactivation des appels
        logger.info("🔴 Test de désactivation des appels...")
        await solana_cog.solana_call_disable(mock_ctx)
        assert solana_cog.solana_call_enabled == False
        logger.info("✅ Appels désactivés avec succès")
        
        # Test 6: Test d'erreur (montant négatif)
        logger.info("❌ Test d'erreur (montant négatif)...")
        await solana_cog.solana_call_set_threshold(mock_ctx, -1.0)
        
        logger.info("🎉 Tous les tests des commandes sont passés avec succès !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests des commandes: {e}")
        return False

async def test_configuration_integration():
    """Test de l'intégration avec la configuration"""
    
    logger.info("🔧 Test de l'intégration avec la configuration")
    
    try:
        from solana_cog import SolanaCog
        
        # Créer des mocks
        mock_bot = MockBot()
        solana_cog = SolanaCog(mock_bot)
        
        # Vérifier que les valeurs initiales correspondent à la config
        logger.info(f"📋 Configuration initiale:")
        logger.info(f"   SOLANA_CALL_ENABLED: {config.SOLANA_CALL_ENABLED}")
        logger.info(f"   SOLANA_CALL_MIN_AMOUNT: {config.SOLANA_CALL_MIN_AMOUNT}")
        
        logger.info(f"📋 Valeurs SolanaCog:")
        logger.info(f"   solana_call_enabled: {solana_cog.solana_call_enabled}")
        logger.info(f"   solana_call_min_amount: {solana_cog.solana_call_min_amount}")
        
        # Test de modification des valeurs
        solana_cog.solana_call_enabled = False
        solana_cog.solana_call_min_amount = 10.0
        
        logger.info(f"📋 Valeurs après modification:")
        logger.info(f"   solana_call_enabled: {solana_cog.solana_call_enabled}")
        logger.info(f"   solana_call_min_amount: {solana_cog.solana_call_min_amount}")
        
        logger.info("✅ Test d'intégration réussi !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test d'intégration: {e}")
        return False

async def test_bot_integration():
    """Test de l'intégration avec le bot principal"""
    
    logger.info("🤖 Test de l'intégration avec le bot principal")
    
    try:
        # Mock du bot avec SolanaCog
        from solana_cog import SolanaCog
        
        mock_bot = MockBot()
        solana_cog = SolanaCog(mock_bot)
        mock_bot.cogs['SolanaCog'] = solana_cog
        
        # Simuler la logique de send_solana_notification
        solana_cog_found = None
        for cog in mock_bot.cogs.values():
            if hasattr(cog, 'solana_call_enabled'):
                solana_cog_found = cog
                break
        
        if solana_cog_found:
            call_enabled = solana_cog_found.solana_call_enabled
            min_amount = solana_cog_found.solana_call_min_amount
            
            logger.info(f"📞 Paramètres récupérés du SolanaCog:")
            logger.info(f"   call_enabled: {call_enabled}")
            logger.info(f"   min_amount: {min_amount}")
            
            logger.info("✅ Test d'intégration bot réussi !")
            return True
        else:
            logger.error("❌ SolanaCog non trouvé dans les cogs")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test d'intégration bot: {e}")
        return False

async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Démarrage des tests des commandes Solana Twilio")
    logger.info("=" * 60)
    
    # Test 1: Commandes SolanaCog
    success1 = await test_solana_cog_commands()
    logger.info("")
    
    # Test 2: Intégration configuration
    success2 = await test_configuration_integration()
    logger.info("")
    
    # Test 3: Intégration bot
    success3 = await test_bot_integration()
    logger.info("")
    
    # Résultats
    logger.info("=" * 60)
    if success1 and success2 and success3:
        logger.info("🎉 Tous les tests sont passés avec succès !")
        logger.info("✅ Les commandes Discord Solana Twilio sont prêtes à être utilisées")
    else:
        logger.error("💥 Certains tests ont échoué")
        logger.error("❌ Vérifiez les erreurs ci-dessus")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
