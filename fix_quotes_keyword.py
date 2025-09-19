#!/usr/bin/env python3
"""
Script pour corriger les guillemets échappés dans bot.py
"""

def fix_quotes():
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer tous les guillemets échappés
    content = content.replace("\\'", "'")
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Guillemets échappés corrigés !")

if __name__ == "__main__":
    fix_quotes()
