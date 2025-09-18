#!/usr/bin/env python3
"""
Script pour corriger la logique de tracking des adresses dans bot.py
"""

import re

def fix_tracking_logic():
    # Lire le fichier
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Code à insérer pour la vérification des adresses trackées
    tracking_code = '''                                # Vérifier si l'adresse du créateur est trackée (PRIORITÉ ABSOLUE)
                                creator_address = None
                                is_tracked_address = False
                                try:
                                    # Extraire l'adresse du créateur depuis l'événement V3
                                    if 'creatorAdmin' in event['args']:
                                        creator_address = event['args']['creatorAdmin']
                                    elif 'msgSender' in event['args']:
                                        creator_address = event['args']['msgSender']
                                    
                                    if creator_address and creator_address in self.tracked_addresses:
                                        is_tracked_address = True
                                        logger.info(f"Adresse trackée V3 détectée : {creator_address} a déployé {name} ({symbol}) {token_address}")
                                        
                                        # Envoyer l'alerte spéciale verte pour les adresses trackées
                                        embed = discord.Embed(
                                            title="🎯 Clanker Adresse Trackée",
                                            description=f"Une adresse que vous surveillez a déployé un nouveau clanker !",
                                            color=discord.Color.green(),
                                            timestamp=datetime.now(timezone.utc)
                                        )
                                        embed.add_field(name="Nom", value=name, inline=True)
                                        embed.add_field(name="Symbole", value=symbol, inline=True)
                                        embed.add_field(name="Contract", value=f"`{token_address}`", inline=False)
                                        embed.add_field(name="Adresse Trackée", value=f"`{creator_address}`", inline=False)
                                        embed.add_field(name="FID", value=fid if fid else "Non spécifié", inline=True)
                                        
                                        if image:
                                            embed.set_thumbnail(url=image)
                                        
                                        # Créer la vue avec les boutons
                                        view = discord.ui.View()
                                        
                                        # Bouton Basescan
                                        basescan_button = discord.ui.Button(
                                            style=discord.ButtonStyle.secondary,
                                            label="Basescan",
                                            url=f"https://basescan.org/token/{token_address}"
                                        )
                                        view.add_item(basescan_button)
                                        
                                        # Bouton Clanker World
                                        clanker_button = discord.ui.Button(
                                            style=discord.ButtonStyle.primary,
                                            label="Lien Clanker World",
                                            url=f"https://www.clanker.world/clanker/{token_address}"
                                        )
                                        view.add_item(clanker_button)
                                        
                                        await channel.send(embed=embed, view=view)
                                        logger.info(f"On-chain Clanker tracked address alert sent for {name} ({symbol}) {token_address} by {creator_address}")
                                        
                                        # Ajout à la surveillance volume
                                        self.tracked_clanker_tokens[token_address.lower()] = {
                                            'first_seen': time.time(),
                                            'alerted': False
                                        }
                                        logger.info(f"[VOLUME TRACK] Ajout du token tracké {token_address.lower()} à la surveillance volume (on-chain)")
                                        continue  # Skip le reste du traitement normal
                                        
                                except Exception as e:
                                    logger.error(f"Erreur lors de l'extraction de l'adresse créateur V3: {e}")
                                
'''
    
    # Code pour V4
    tracking_code_v4 = '''                                # Vérifier si l'adresse du créateur est trackée (PRIORITÉ ABSOLUE)
                                creator_address = None
                                is_tracked_address = False
                                try:
                                    # Extraire l'adresse du créateur depuis l'événement V4
                                    if 'tokenAdmin' in event['args']:
                                        creator_address = event['args']['tokenAdmin']
                                    elif 'msgSender' in event['args']:
                                        creator_address = event['args']['msgSender']
                                    
                                    if creator_address and creator_address in self.tracked_addresses:
                                        is_tracked_address = True
                                        logger.info(f"Adresse trackée V4 détectée : {creator_address} a déployé {name} ({symbol}) {token_address}")
                                        
                                        # Envoyer l'alerte spéciale verte pour les adresses trackées V4
                                        embed = discord.Embed(
                                            title="🎯 Clanker Adresse Trackée (V4)",
                                            description=f"Une adresse que vous surveillez a déployé un nouveau clanker V4 !",
                                            color=discord.Color.green(),
                                            timestamp=datetime.now(timezone.utc)
                                        )
                                        embed.add_field(name="Nom", value=name, inline=True)
                                        embed.add_field(name="Symbole", value=symbol, inline=True)
                                        embed.add_field(name="Contract", value=f"`{token_address}`", inline=False)
                                        embed.add_field(name="Adresse Trackée", value=f"`{creator_address}`", inline=False)
                                        embed.add_field(name="FID", value=fid if fid else "Non spécifié", inline=True)
                                        
                                        if image:
                                            embed.set_thumbnail(url=image)
                                        
                                        # Créer la vue avec les boutons
                                        view = discord.ui.View()
                                        
                                        # Bouton Basescan
                                        basescan_button = discord.ui.Button(
                                            style=discord.ButtonStyle.secondary,
                                            label="Basescan",
                                            url=f"https://basescan.org/token/{token_address}"
                                        )
                                        view.add_item(basescan_button)
                                        
                                        # Bouton Clanker World
                                        clanker_button = discord.ui.Button(
                                            style=discord.ButtonStyle.primary,
                                            label="Lien Clanker World",
                                            url=f"https://www.clanker.world/clanker/{token_address}"
                                        )
                                        view.add_item(clanker_button)
                                        
                                        await channel.send(embed=embed, view=view)
                                        logger.info(f"On-chain Clanker V4 tracked address alert sent for {name} ({symbol}) {token_address} by {creator_address}")
                                        
                                        # Ajout à la surveillance volume
                                        self.tracked_clanker_tokens[token_address.lower()] = {
                                            'first_seen': time.time(),
                                            'alerted': False
                                        }
                                        logger.info(f"[VOLUME TRACK] Ajout du token V4 tracké {token_address.lower()} à la surveillance volume (on-chain)")
                                        continue  # Skip le reste du traitement normal
                                        
                                except Exception as e:
                                    logger.error(f"Erreur lors de l'extraction de l'adresse créateur V4: {e}")
                                
'''
    
    # Remplacer la première occurrence (V3)
    pattern1 = r'(                                except Exception:\n                                    pass\n)(                                # --- Filtrage banlist/whitelist ---)'
    replacement1 = r'\1\n' + tracking_code + r'\2'
    content = re.sub(pattern1, replacement1, content, count=1)
    
    # Remplacer la seconde occurrence (V4)
    pattern2 = r'(                                except Exception:\n                                    pass\n)(                                # --- Filtrage banlist/whitelist ---)'
    replacement2 = r'\1\n' + tracking_code_v4 + r'\2'
    content = re.sub(pattern2, replacement2, content, count=1)
    
    # Écrire le fichier modifié
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Modifications appliquées avec succès !")

if __name__ == "__main__":
    fix_tracking_logic()
