#!/usr/bin/env python3
"""
Script pour corriger la base de données de production
Ce script peut être exécuté directement sur le serveur
"""

import os
import sys

def fix_production_database():
    """Corrige la base de données de production"""
    
    print("🚀 Correction de la base de données de production...")
    
    # Vérifier si nous sommes sur le serveur de production
    if not os.getenv('DATABASE_URL'):
        print("❌ Variable d'environnement DATABASE_URL non trouvée")
        print("💡 Assurez-vous d'exécuter ce script sur le serveur de production")
        return False
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        database_url = os.getenv('DATABASE_URL')
        print(f"📋 Connexion à la base de données PostgreSQL...")
        
        # Connexion à la base de données
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        # Vérifier la structure actuelle
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'active_snipes'
            ORDER BY ordinal_position;
        """)
        
        columns = c.fetchall()
        print(f"📋 Structure actuelle: {columns}")
        
        # Si la table a l'ancienne structure
        if len(columns) == 3 and any('fid' in col[0] for col in columns):
            print("🔄 Migration de l'ancienne structure...")
            
            # Supprimer l'ancienne table
            c.execute("DROP TABLE IF EXISTS active_snipes CASCADE")
            print("✅ Ancienne table supprimée")
            
            # Créer la table tracked_addresses
            c.execute("""
                CREATE TABLE IF NOT EXISTS tracked_addresses (
                    address VARCHAR(42) PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Table tracked_addresses créée")
            
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
        print(f"📋 Nouvelle structure: {new_columns}")
        
        conn.close()
        
        print("🎉 Base de données de production corrigée !")
        return True
        
    except ImportError:
        print("❌ psycopg2 non installé. Installation...")
        os.system("pip install psycopg2-binary")
        return fix_production_database()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = fix_production_database()
    if success:
        print("\n✨ La base de données est maintenant prête !")
        print("🎯 Redémarrez votre bot pour que les changements prennent effet.")
    else:
        print("\n❌ Échec de la correction.")
        sys.exit(1)
