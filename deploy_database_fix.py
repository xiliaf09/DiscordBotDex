#!/usr/bin/env python3
"""
Script de déploiement pour corriger la base de données de production
"""

import os
import subprocess
import sys

def deploy_database_fix():
    """Déploie la correction de la base de données"""
    
    print("🚀 Déploiement de la correction de base de données...")
    
    # Vérifier si nous sommes sur le serveur de production
    if not os.getenv('DATABASE_URL'):
        print("❌ Variable d'environnement DATABASE_URL non trouvée")
        print("💡 Ce script doit être exécuté sur le serveur de production")
        return False
    
    try:
        # Option 1: Exécuter le script Python de migration
        print("🔧 Exécution du script de migration Python...")
        result = subprocess.run([sys.executable, "migrate_postgresql.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration Python réussie")
            print(result.stdout)
            return True
        else:
            print("❌ Échec de la migration Python")
            print(result.stderr)
            
            # Option 2: Exécuter le script SQL directement
            print("🔧 Tentative avec le script SQL...")
            return execute_sql_script()
            
    except Exception as e:
        print(f"❌ Erreur lors du déploiement: {e}")
        return False

def execute_sql_script():
    """Exécute le script SQL directement"""
    
    try:
        import psycopg2
        
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        c = conn.cursor()
        
        # Lire et exécuter le script SQL
        with open('fix_database.sql', 'r') as f:
            sql_script = f.read()
        
        # Exécuter chaque commande SQL séparément
        commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
        
        for command in commands:
            if command.upper().startswith('SELECT'):
                # Pour les SELECT, afficher les résultats
                c.execute(command)
                results = c.fetchall()
                print(f"📋 Résultat: {results}")
            else:
                # Pour les autres commandes, les exécuter
                c.execute(command)
                print(f"✅ Commande exécutée: {command[:50]}...")
        
        conn.close()
        print("🎉 Script SQL exécuté avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du script SQL: {e}")
        return False

if __name__ == "__main__":
    success = deploy_database_fix()
    if success:
        print("\n✨ La base de données de production est maintenant corrigée !")
        print("🎯 Redémarrez votre bot pour que les changements prennent effet.")
    else:
        print("\n❌ Échec du déploiement.")
        print("💡 Vous pouvez exécuter manuellement le script SQL sur votre base de données.")
        sys.exit(1)
