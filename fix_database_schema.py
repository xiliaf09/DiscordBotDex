#!/usr/bin/env python3
"""
Script de migration pour corriger la structure de la base de données
"""

import os
import psycopg2
import sqlite3
from config import *

def fix_database_schema():
    """Corrige la structure de la base de données"""
    
    # Vérifier le type de base de données
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql://'):
        print("🔧 Correction de la structure PostgreSQL...")
        fix_postgresql_schema(database_url)
    else:
        print("🔧 Correction de la structure SQLite...")
        fix_sqlite_schema()

def fix_postgresql_schema(database_url):
    """Corrige la structure PostgreSQL"""
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # Vérifier si la table active_snipes existe et sa structure
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
            
            # Créer la nouvelle structure
            c.execute("""
                CREATE TABLE IF NOT EXISTS tracked_addresses (
                    address VARCHAR(42) PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            c.execute("""
                CREATE TABLE IF NOT EXISTS active_snipes (
                    id SERIAL PRIMARY KEY,
                    tracked_address VARCHAR(42) NOT NULL,
                    snipe_amount_eth DECIMAL(18,8) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (tracked_address) REFERENCES tracked_addresses(address)
                )
            """)
            
            print("✅ Nouvelle structure créée avec succès")
            
        else:
            print("✅ Structure déjà correcte")
        
        conn.commit()
        conn.close()
        print("🎉 Migration PostgreSQL terminée avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration PostgreSQL: {e}")

def fix_sqlite_schema():
    """Corrige la structure SQLite"""
    try:
        conn = sqlite3.connect('snipes.db')
        c = conn.cursor()
        
        # Vérifier la structure actuelle
        c.execute("PRAGMA table_info(active_snipes)")
        columns = c.fetchall()
        print(f"📋 Colonnes actuelles dans active_snipes: {columns}")
        
        # Si la table a l'ancienne structure
        if len(columns) == 3 and any('fid' in col[1] for col in columns):
            print("🔄 Migration de l'ancienne structure vers la nouvelle...")
            
            # Supprimer l'ancienne table
            c.execute("DROP TABLE IF EXISTS active_snipes")
            
            # Créer la nouvelle structure
            c.execute("""
                CREATE TABLE IF NOT EXISTS tracked_addresses (
                    address TEXT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            c.execute("""
                CREATE TABLE IF NOT EXISTS active_snipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracked_address TEXT NOT NULL,
                    snipe_amount_eth REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (tracked_address) REFERENCES tracked_addresses(address)
                )
            """)
            
            print("✅ Nouvelle structure créée avec succès")
            
        else:
            print("✅ Structure déjà correcte")
        
        conn.commit()
        conn.close()
        print("🎉 Migration SQLite terminée avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration SQLite: {e}")

if __name__ == "__main__":
    print("🚀 Début de la correction de la structure de base de données...")
    fix_database_schema()
    print("✨ Correction terminée !")
