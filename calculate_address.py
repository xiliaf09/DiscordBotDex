#!/usr/bin/env python3
"""
Script pour calculer l'adresse du wallet à partir de la clé privée
"""

from eth_account import Account

def calculate_wallet_address(private_key):
    """Calcule l'adresse du wallet à partir de la clé privée"""
    try:
        # Créer un compte à partir de la clé privée
        account = Account.from_key(private_key)
        return account.address
    except Exception as e:
        print(f"Erreur lors du calcul de l'adresse: {e}")
        return None

if __name__ == "__main__":
    private_key = "0x77c59724588bdde9dc0aaaafe91902fd1d8bc6b29d51d69a06c989e091f80814"
    
    print("🔑 Calcul de l'adresse du wallet...")
    print(f"Clé privée: {private_key}")
    
    address = calculate_wallet_address(private_key)
    
    if address:
        print(f"✅ Adresse du wallet: {address}")
    else:
        print("❌ Impossible de calculer l'adresse")
