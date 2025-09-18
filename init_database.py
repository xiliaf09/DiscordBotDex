#!/usr/bin/env python3
"""
Script pour initialiser la base de données avec la bonne structure
"""

import sqlite3
import os

def init_database():
    """Initialise la base de données avec la structure correcte"""
    print("🚀 Initialisation de la base de données...")
    
    try:
        # Supprimer l'ancienne base de données si elle existe
        if os.path.exists('snipes.db'):
            os.remove('snipes.db')
            print("🗑️ Ancienne base de données supprimée")
        
        # Créer une nouvelle base de données
        conn = sqlite3.connect('snipes.db')
        c = conn.cursor()
        
        # Créer la table tracked_addresses
        c.execute("""
            CREATE TABLE tracked_addresses (
                address TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table tracked_addresses créée")
        
        # Créer la table active_snipes
        c.execute("""
            CREATE TABLE active_snipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracked_address TEXT NOT NULL,
                snipe_amount_eth REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (tracked_address) REFERENCES tracked_addresses(address)
            )
        """)
        print("✅ Table active_snipes créée")
        
        # Créer les autres tables nécessaires
        c.execute("""
            CREATE TABLE banned_fids (
                fid TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table banned_fids créée")
        
        c.execute("""
            CREATE TABLE whitelisted_fids (
                fid TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table whitelisted_fids créée")
        
        c.execute("""
            CREATE TABLE keyword_whitelist (
                keyword TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table keyword_whitelist créée")
        
        c.execute("""
            CREATE TABLE bot_preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table bot_preferences créée")
        
        # Tester l'insertion d'une adresse trackée
        test_address = "0x38B3890A0C0983bE825E353b809A96aC4fA0077e"
        c.execute("INSERT INTO tracked_addresses (address) VALUES (?)", (test_address,))
        print(f"✅ Adresse test ajoutée: {test_address}")
        
        # Tester l'insertion d'un snipe
        c.execute("""
            INSERT INTO active_snipes 
            (tracked_address, snipe_amount_eth, is_active) 
            VALUES (?, ?, ?)
        """, (test_address, 0.001, 1))
        print(f"✅ Snipe test ajouté: {test_address} - 0.001 ETH")
        
        # Vérifier les données
        c.execute("SELECT * FROM tracked_addresses")
        tracked = c.fetchall()
        print(f"📋 Adresses trackées: {tracked}")
        
        c.execute("SELECT * FROM active_snipes")
        snipes = c.fetchall()
        print(f"📋 Snipes actifs: {snipes}")
        
        conn.commit()
        conn.close()
        
        print("🎉 Base de données initialisée avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n✨ La base de données est prête pour la commande setupsnipe !")
    else:
        print("\n❌ Échec de l'initialisation de la base de données.")
