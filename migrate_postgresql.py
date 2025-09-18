#!/usr/bin/env python3
"""
Script de migration PostgreSQL pour corriger la structure de la base de données
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate_postgresql_database():
    """Migre la base de données PostgreSQL vers la nouvelle structure"""
    
    # Récupérer l'URL de la base de données depuis les variables d'environnement
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Variable d'environnement DATABASE_URL non trouvée")
        return False
    
    if not database_url.startswith('postgresql://'):
        print("❌ DATABASE_URL n'est pas une URL PostgreSQL")
        return False
    
    print(f"🔧 Migration de la base de données PostgreSQL...")
    print(f"📋 URL: {database_url[:20]}...")
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        # Vérifier la structure actuelle de active_snipes
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'active_snipes'
            ORDER BY ordinal_position;
        """)
        
        columns = c.fetchall()
        print(f"📋 Colonnes actuelles dans active_snipes: {columns}")
        
        # Si la table a l'ancienne structure (fid, amount, timestamp)
        if len(columns) == 3 and any('fid' in col[0] for col in columns):
            print("🔄 Migration de l'ancienne structure vers la nouvelle...")
            
            # Supprimer l'ancienne table
            c.execute("DROP TABLE IF EXISTS active_snipes CASCADE")
            print("✅ Ancienne table active_snipes supprimée")
            
            # Créer la table tracked_addresses si elle n'existe pas
            c.execute("""
                CREATE TABLE IF NOT EXISTS tracked_addresses (
                    address VARCHAR(42) PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Table tracked_addresses créée/vérifiée")
            
            # Créer la nouvelle table active_snipes
            c.execute("""
                CREATE TABLE active_snipes (
                    id SERIAL PRIMARY KEY,
                    tracked_address VARCHAR(42) NOT NULL,
                    snipe_amount_eth DECIMAL(18,8) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (tracked_address) REFERENCES tracked_addresses(address)
                )
            """)
            print("✅ Nouvelle table active_snipes créée")
            
        elif len(columns) == 0:
            print("🔄 Création des tables manquantes...")
            
            # Créer la table tracked_addresses
            c.execute("""
                CREATE TABLE IF NOT EXISTS tracked_addresses (
                    address VARCHAR(42) PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Table tracked_addresses créée")
            
            # Créer la table active_snipes
            c.execute("""
                CREATE TABLE active_snipes (
                    id SERIAL PRIMARY KEY,
                    tracked_address VARCHAR(42) NOT NULL,
                    snipe_amount_eth DECIMAL(18,8) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (tracked_address) REFERENCES tracked_addresses(address)
                )
            """)
            print("✅ Table active_snipes créée")
            
        else:
            print("✅ Structure déjà correcte")
        
        # Vérifier la nouvelle structure
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'active_snipes'
            ORDER BY ordinal_position;
        """)
        
        new_columns = c.fetchall()
        print(f"📋 Nouvelle structure active_snipes: {new_columns}")
        
        # Tester l'insertion d'une adresse trackée
        test_address = "0x38B3890A0C0983bE825E353b809A96aC4fA0077e"
        c.execute("INSERT INTO tracked_addresses (address) VALUES (%s) ON CONFLICT (address) DO NOTHING", (test_address,))
        print(f"✅ Adresse test ajoutée: {test_address}")
        
        # Tester l'insertion d'un snipe
        c.execute("""
            INSERT INTO active_snipes 
            (tracked_address, snipe_amount_eth, is_active) 
            VALUES (%s, %s, %s)
        """, (test_address, 0.001, True))
        print(f"✅ Snipe test ajouté: {test_address} - 0.001 ETH")
        
        # Vérifier les données
        c.execute("SELECT * FROM tracked_addresses WHERE address = %s", (test_address,))
        tracked = c.fetchone()
        print(f"📋 Adresse trackée: {tracked}")
        
        c.execute("SELECT * FROM active_snipes WHERE tracked_address = %s", (test_address,))
        snipes = c.fetchone()
        print(f"📋 Snipe actif: {snipes}")
        
        conn.close()
        
        print("🎉 Migration PostgreSQL terminée avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Début de la migration PostgreSQL...")
    success = migrate_postgresql_database()
    if success:
        print("\n✨ La base de données PostgreSQL est maintenant prête !")
        print("🎯 La commande !setupsnipe devrait maintenant fonctionner.")
    else:
        print("\n❌ Échec de la migration PostgreSQL.")
