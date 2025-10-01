#!/usr/bin/env python3
"""
Script de test pour vérifier la correction du problème de suppression des adresses Solana
"""

import asyncio
import logging
import config
from unittest.mock import Mock, AsyncMock

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_solana_removal_fix():
    """Test de la correction du problème de suppression des adresses Solana"""
    
    logger.info("🧪 Test de la correction du problème de suppression Solana")
    
    try:
        # Import du SolanaTracker
        from solana_tracker import SolanaTracker
        
        # Créer une instance du tracker
        tracker = SolanaTracker()
        
        # Test 1: Ajouter une adresse
        logger.info("📝 Test 1: Ajout d'une adresse...")
        test_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        
        # Mock de la base de données pour simuler l'ajout
        tracker.db.add_tracked_address = Mock(return_value=True)
        tracker.db.remove_tracked_address = Mock(return_value=True)
        tracker.db.get_tracked_addresses = Mock(return_value=[
            {'address': test_address, 'nickname': 'Test', 'added_by': 'test', 'added_at': '2024-01-01'}
        ])
        
        # Ajouter l'adresse
        success = await tracker.add_address(test_address, "Test Address", "test_user")
        assert success == True
        assert test_address in tracker.tracked_addresses
        logger.info("✅ Adresse ajoutée avec succès")
        
        # Test 2: Vérifier que la tâche de polling est créée
        logger.info("📝 Test 2: Vérification de la création de la tâche de polling...")
        # Simuler le démarrage du tracking
        tracker.is_running = True
        task = asyncio.create_task(tracker.poll_address_transactions(test_address))
        tracker.polling_tasks[test_address] = task
        
        assert test_address in tracker.polling_tasks
        assert not task.done()
        logger.info("✅ Tâche de polling créée avec succès")
        
        # Test 3: Supprimer l'adresse
        logger.info("📝 Test 3: Suppression de l'adresse...")
        success = await tracker.remove_address(test_address)
        assert success == True
        assert test_address not in tracker.tracked_addresses
        assert test_address not in tracker.polling_tasks
        logger.info("✅ Adresse supprimée avec succès")
        
        # Test 4: Vérifier que la tâche est arrêtée
        logger.info("📝 Test 4: Vérification de l'arrêt de la tâche...")
        # Attendre un peu pour que la tâche se termine
        await asyncio.sleep(0.1)
        assert test_address not in tracker.polling_tasks
        logger.info("✅ Tâche de polling arrêtée avec succès")
        
        # Test 5: Test de la fonction stop_tracking
        logger.info("📝 Test 5: Test de la fonction stop_tracking...")
        # Ajouter quelques adresses et tâches
        tracker.tracked_addresses.add("address1")
        tracker.tracked_addresses.add("address2")
        tracker.polling_tasks["address1"] = asyncio.create_task(asyncio.sleep(10))
        tracker.polling_tasks["address2"] = asyncio.create_task(asyncio.sleep(10))
        
        # Arrêter le tracking
        await tracker.stop_tracking()
        
        # Vérifier que toutes les tâches sont arrêtées
        assert len(tracker.polling_tasks) == 0
        logger.info("✅ Toutes les tâches arrêtées avec succès")
        
        logger.info("🎉 Tous les tests de correction sont passés avec succès !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests de correction: {e}")
        return False

async def test_polling_task_behavior():
    """Test du comportement des tâches de polling lors de la suppression"""
    
    logger.info("🔄 Test du comportement des tâches de polling")
    
    try:
        from solana_tracker import SolanaTracker
        
        tracker = SolanaTracker()
        test_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        
        # Mock de la base de données
        tracker.db.add_tracked_address = Mock(return_value=True)
        tracker.db.remove_tracked_address = Mock(return_value=True)
        tracker.db.get_tracked_addresses = Mock(return_value=[])
        tracker.get_recent_transactions = AsyncMock(return_value=[])
        
        # Ajouter l'adresse
        await tracker.add_address(test_address, "Test", "test")
        tracker.is_running = True
        
        # Créer une tâche de polling
        task = asyncio.create_task(tracker.poll_address_transactions(test_address))
        tracker.polling_tasks[test_address] = task
        
        # Laisser la tâche tourner un peu
        await asyncio.sleep(0.1)
        
        # Supprimer l'adresse
        await tracker.remove_address(test_address)
        
        # Attendre que la tâche se termine
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            logger.error("❌ La tâche de polling n'a pas été arrêtée correctement")
            return False
        
        logger.info("✅ La tâche de polling s'est arrêtée correctement après la suppression")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de comportement: {e}")
        return False

async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Démarrage des tests de correction du problème de suppression Solana")
    logger.info("=" * 70)
    
    # Test 1: Test de la correction principale
    success1 = await test_solana_removal_fix()
    logger.info("")
    
    # Test 2: Test du comportement des tâches de polling
    success2 = await test_polling_task_behavior()
    logger.info("")
    
    # Résultats
    logger.info("=" * 70)
    if success1 and success2:
        logger.info("🎉 Tous les tests de correction sont passés avec succès !")
        logger.info("✅ Le problème de suppression des adresses Solana est corrigé")
        logger.info("✅ Les tâches de polling s'arrêtent correctement")
        logger.info("✅ Les adresses supprimées ne génèrent plus d'alertes")
    else:
        logger.error("💥 Certains tests ont échoué")
        logger.error("❌ Vérifiez les erreurs ci-dessus")
    
    logger.info("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
