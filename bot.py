import os
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set
import time
import sys

import discord
from discord.ext import tasks, commands
import requests
from dotenv import load_dotenv
import httpx
import feedparser
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
BASESCAN_API_KEY = os.getenv('BASESCAN_API_KEY')

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
TRUTH_SOCIAL_RSS_URL = "https://truthsocial.com/users/realDonaldTrump/feed.rss"
CLANKER_API_URL = "https://www.clanker.world/api"
BASESCAN_API_URL = "https://api.basescan.org/api"
WARPCAST_API_URL = "https://client.warpcast.com/v2"
MONITORED_CHAINS = {
    "base": "Base",
    "solana": "Solana"
}
POLL_INTERVAL = 2  # seconds
SEEN_TOKENS_FILE = "seen_tokens.json"
SEEN_CLANKER_TOKENS_FILE = "seen_clanker_tokens.json"
TRACKED_WALLETS_FILE = "tracked_wallets.json"
BANNED_FIDS_FILE = "banned_fids.json"
WHITELISTED_FIDS_FILE = "whitelisted_fids.json"

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))

class TokenMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen_tokens: Set[str] = self._load_seen_tokens()
        self.channel = None
        self.active_chains = {
            "base": True,
            "solana": True
        }
        self.seen_trump_posts = set()
        self.last_check_time = None
        
        # Liste des tickers crypto à surveiller
        self.crypto_tickers = {
            'BTC', 'ETH', 'XRP', 'SOL', 'SUI', 'DOGE', 'SHIB', 'BNB', 'ADA',
            'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'XLM', 'ATOM'
        }

    def _load_seen_tokens(self) -> Set[str]:
        """Load previously seen token addresses from file."""
        try:
            if os.path.exists(SEEN_TOKENS_FILE):
                with open(SEEN_TOKENS_FILE, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Error loading seen tokens: {e}")
            return set()

    def _save_seen_tokens(self):
        """Save seen token addresses to file."""
        try:
            with open(SEEN_TOKENS_FILE, 'w') as f:
                json.dump(list(self.seen_tokens), f)
        except Exception as e:
            logger.error(f"Error saving seen tokens: {e}")

    @commands.command()
    async def baseon(self, ctx):
        """Activer le monitoring pour Base"""
        self.active_chains["base"] = True
        await ctx.send("✅ Monitoring activé pour Base")

    @commands.command()
    async def baseoff(self, ctx):
        """Désactiver le monitoring pour Base"""
        self.active_chains["base"] = False
        await ctx.send("❌ Monitoring désactivé pour Base")

    @commands.command()
    async def solanaon(self, ctx):
        """Activer le monitoring pour Solana"""
        self.active_chains["solana"] = True
        await ctx.send("✅ Monitoring activé pour Solana")

    @commands.command()
    async def solanaoff(self, ctx):
        """Désactiver le monitoring pour Solana"""
        self.active_chains["solana"] = False
        await ctx.send("❌ Monitoring désactivé pour Solana")

    @commands.command()
    async def status(self, ctx):
        """Afficher le statut du monitoring pour chaque chaîne"""
        status_message = "📊 Statut du monitoring:\n"
        for chain_id, is_active in self.active_chains.items():
            chain_name = MONITORED_CHAINS[chain_id]
            status = "✅ Activé" if is_active else "❌ Désactivé"
            status_message += f"{chain_name}: {status}\n"
        await ctx.send(status_message)

    @commands.command()
    async def test(self, ctx):
        """Send a test notification"""
        try:
            embed = discord.Embed(
                title="Test Notification",
                description="Ceci est un message test du bot DexBaseBot!",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(
                name="Status",
                value="✅ Le bot fonctionne correctement!",
                inline=False
            )
            await ctx.send(embed=embed)
            logger.info("Test notification sent successfully")
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            await ctx.send("❌ Erreur lors de l'envoi du message test.")

    @commands.command()
    async def lasttoken(self, ctx):
        """Fetch and display the latest token from the API"""
        try:
            # Send initial message
            status_msg = await ctx.send("🔍 Recherche du dernier token...")
            
            # Fetch latest tokens
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0'
            }
            
            response = requests.get(DEXSCREENER_API_URL, headers=headers)
            response.raise_for_status()
            tokens = response.json()

            # Find the latest token from monitored chains
            latest_token = None
            for token in tokens:
                chain_id = token.get('chainId', '').lower()
                if chain_id in MONITORED_CHAINS and self.active_chains.get(chain_id, False):
                    latest_token = token
                    break

            if latest_token:
                # Delete the status message
                await status_msg.delete()
                # Send token notification
                await self._send_token_notification(latest_token, ctx.channel, "📊 Dernier Token sur")
            else:
                await status_msg.edit(content="❌ Aucun token récent trouvé sur Base ou Solana.")

        except Exception as e:
            logger.error(f"Error fetching latest token: {e}")
            if status_msg:
                await status_msg.edit(content="❌ Erreur lors de la recherche du dernier token.")
            else:
                await ctx.send("❌ Erreur lors de la recherche du dernier token.")

    @commands.command()
    async def lasttrump(self, ctx):
        """Fetch and display the latest post from Trump on Truth Social"""
        try:
            # Send initial message
            status_msg = await ctx.send("🔍 Recherche du dernier post de Trump...")
            logger.info("Attempting to fetch Trump's posts from Truth Social RSS")
            
            # Using Truth Social RSS feed to get Trump's recent posts
            feed = feedparser.parse(TRUTH_SOCIAL_RSS_URL)
            logger.info(f"RSS Feed Status: Version={feed.version}, Status={feed.get('status', 'N/A')}")
            logger.info(f"Feed entries found: {len(feed.entries)}")
            
            if not feed.entries:
                logger.warning("No entries found in the RSS feed")
                await status_msg.edit(content="❌ Aucun post récent trouvé de Trump.")
                return
            
            # Get the latest post
            latest_post = feed.entries[0]
            logger.info(f"Latest post found with title: {latest_post.get('title', 'No title')}")
            
            try:
                post_id = latest_post.id.split('/')[-1]  # Extract post ID from the URL
            except (AttributeError, IndexError):
                post_id = "unknown"
                logger.warning("Could not extract post ID from feed entry")
            
            content = latest_post.get('description', latest_post.get('summary', latest_post.get('title', 'No content available')))
            logger.info(f"Content length: {len(content)}")
            
            # Recherche des tickers crypto dans le post
            found_tickers = set()
            words = content.split()
            for word in words:
                # Enlever le $ si présent et convertir en majuscules
                ticker = word.strip('$').upper()
                if ticker in self.crypto_tickers:
                    found_tickers.add(ticker)
            
            if found_tickers:
                logger.info(f"Found crypto tickers in post: {found_tickers}")
            
            # Delete the status message
            await status_msg.delete()
            
            # Create and send embed
            embed = discord.Embed(
                title="🔄 Dernier Post de Trump",
                description="Dernier post de Donald Trump sur Truth Social",
                color=discord.Color.gold(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="Message",
                value=content[:1000] + "..." if len(content) > 1000 else content,
                inline=False
            )
            
            if found_tickers:
                embed.add_field(
                    name="Cryptos mentionnées",
                    value=", ".join([f"${ticker}" for ticker in found_tickers]),
                    inline=False
                )
            
            post_link = latest_post.get('link', f"https://truthsocial.com/@realDonaldTrump/posts/{post_id}")
            embed.add_field(
                name="Lien",
                value=post_link,
                inline=False
            )
            
            await ctx.send(embed=embed)
            logger.info(f"Successfully sent latest Trump post notification with ID {post_id}")
            
        except Exception as e:
            logger.error(f"Error fetching latest Trump post: {str(e)}", exc_info=True)
            if status_msg:
                await status_msg.edit(content="❌ Erreur lors de la recherche du dernier post de Trump.")
            else:
                await ctx.send("❌ Erreur lors de la recherche du dernier post de Trump.")

    async def _send_token_notification(self, token: Dict, channel: discord.TextChannel, title_prefix="🆕 Nouveau Token Détecté"):
        """Send a Discord notification for a token."""
        try:
            chain_id = token['chainId'].lower()
            chain_name = MONITORED_CHAINS.get(chain_id, chain_id)
            
            # Set color based on chain
            color = discord.Color.blue() if chain_id == 'base' else discord.Color.orange()
            
            embed = discord.Embed(
                title=f"{title_prefix} {chain_name}",
                color=color,
                timestamp=datetime.now(timezone.utc)
            )

            # Add token information
            if token.get('description'):
                embed.description = token['description']

            embed.add_field(
                name="📝 Adresse du Token",
                value=f"`{token['tokenAddress']}`",
                inline=False
            )

            # Add chain indicator emoji
            chain_emoji = "⚡" if chain_id == 'base' else "☀️"
            embed.add_field(
                name="Blockchain",
                value=f"{chain_emoji} {chain_name}",
                inline=True
            )

            # Add links if available
            if token.get('links'):
                links_text = ""
                for link in token['links']:
                    if link.get('type') and link.get('url'):
                        links_text += f"[{link['type']}]({link['url']})\n"
                if links_text:
                    embed.add_field(
                        name="🔗 Liens",
                        value=links_text,
                        inline=False
                    )

            # Add Dexscreener link
            if token.get('url'):
                dexscreener_url = token['url']
            else:
                chain_path = 'base' if chain_id == 'base' else 'solana'
                dexscreener_url = f"https://dexscreener.com/{chain_path}/{token['tokenAddress']}"
            
            embed.add_field(
                name="🔍 Dexscreener",
                value=f"[Voir sur Dexscreener]({dexscreener_url})",
                inline=False
            )

            # Set thumbnail if icon is available
            if token.get('icon'):
                embed.set_thumbnail(url=token['icon'])

            # Add social context if available
            social_context = token.get('social_context', {})
            platform = social_context.get('platform', 'Unknown')
            interface = social_context.get('interface', 'Unknown')
            username = social_context.get('username')
            embed.add_field(
                name="Déployé via",
                value=f"{platform} ({interface})",
                inline=True
            )

            # Add username with Warpcast link if available
            if username and platform.lower() == "farcaster":
                embed.add_field(
                    name="Username",
                    value=f"[@{username}](https://warpcast.com/{username})",
                    inline=True
                )

            # Add market cap if available
            if market_cap := token.get('starting_market_cap'):
                embed.add_field(
                    name="Market Cap Initial",
                    value=f"${market_cap:,.2f}",
                    inline=True
                )

            # Create view with buttons
            view = discord.ui.View()
            
            # Add Photon button if pool address is available
            if token.get('pool_address'):
                photon_url = f"https://photon-base.tinyastro.io/en/lp/{token['pool_address']}"
                photon_button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Voir sur Photon",
                    url=photon_url
                )
                view.add_item(photon_button)

            await channel.send(embed=embed, view=view)
            logger.info(f"Sent notification for {chain_name} token at address {token['tokenAddress']}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            await channel.send("❌ Erreur lors de l'envoi de la notification du token.")

    @tasks.loop(seconds=POLL_INTERVAL)
    async def monitor_tokens(self):
        """Monitor for new tokens on monitored blockchains."""
        try:
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0'
            }
            
            logger.info("Fetching latest token profiles...")
            response = requests.get(DEXSCREENER_API_URL, headers=headers)
            response.raise_for_status()
            tokens = response.json()
            logger.info(f"Received {len(tokens)} tokens from API")

            # Filter for monitored blockchain tokens
            new_tokens = []
            for token in tokens:
                chain_id = token.get('chainId', '').lower()
                token_address = token.get('tokenAddress')
                
                if chain_id in MONITORED_CHAINS and token_address and self.active_chains.get(chain_id, False):
                    token_key = f"{chain_id}:{token_address}"
                    if token_key not in self.seen_tokens:
                        new_tokens.append(token)
                        self.seen_tokens.add(token_key)
                        logger.info(f"New token detected - Chain: {chain_id}, Address: {token_address}")

            # Process new tokens
            for token in new_tokens:
                await self._send_token_notification(token, self.channel)

            # Save updated seen tokens
            self._save_seen_tokens()

            if new_tokens:
                logger.info(f"Found {len(new_tokens)} new tokens")
            else:
                logger.debug("No new tokens found")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tokens: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    @monitor_tokens.before_loop
    async def before_monitor_tokens(self):
        """Wait until the bot is ready before starting the monitor."""
        await self.bot.wait_until_ready()
        self.channel = self.bot.get_channel(CHANNEL_ID)
        if not self.channel:
            logger.error(f"Could not find channel with ID {CHANNEL_ID}")
            return

    @tasks.loop(seconds=10)
    async def check_trump_posts(self):
        try:
            # Using Truth Social RSS feed to get Trump's recent posts
            feed = feedparser.parse(TRUTH_SOCIAL_RSS_URL)
            
            for entry in feed.entries:
                post_id = entry.id.split('/')[-1]  # Extract post ID from the URL
                
                # Skip if we've already seen this post
                if post_id in self.seen_trump_posts:
                    continue
                    
                content = entry.description
                
                # Recherche des tickers crypto dans le post
                found_tickers = set()
                words = content.split()
                for word in words:
                    # Enlever le $ si présent et convertir en majuscules
                    ticker = word.strip('$').upper()
                    if ticker in self.crypto_tickers:
                        found_tickers.add(ticker)
                
                # Si des tickers sont trouvés, envoyer une notification
                if found_tickers:
                    channel = self.bot.get_channel(int(os.getenv('CHANNEL_ID')))
                    
                    if channel:
                        embed = discord.Embed(
                            title="🚨 Trump mentionne des cryptos!",
                            description=f"Donald Trump vient de mentionner des cryptos sur Truth Social!",
                            color=discord.Color.gold()
                        )
                        
                        embed.add_field(
                            name="Cryptos mentionnées",
                            value=", ".join([f"${ticker}" for ticker in found_tickers]),
                            inline=False
                        )
                        
                        embed.add_field(
                            name="Message",
                            value=content[:1000] + "..." if len(content) > 1000 else content,
                            inline=False
                        )
                        
                        embed.add_field(
                            name="Lien",
                            value=entry.link,
                            inline=False
                        )
                        
                        await channel.send(embed=embed)
                
                # Ajouter le post aux posts vus
                self.seen_trump_posts.add(post_id)
                
            # Garder seulement les 100 derniers posts en mémoire
            if len(self.seen_trump_posts) > 100:
                self.seen_trump_posts = set(list(self.seen_trump_posts)[-100:])
                
        except Exception as e:
            logger.error(f"Error checking Trump posts: {e}")

    @check_trump_posts.before_loop
    async def before_check_trump_posts(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def help(self, ctx):
        """Affiche la liste des commandes disponibles et leur explication dans un embed."""
        embed = discord.Embed(
            title="Aide - Commandes disponibles",
            color=discord.Color.green()
        )
        embed.add_field(name="!help", value="Affiche cette aide.", inline=False)
        embed.add_field(name="!test", value="Vérifie que le bot fonctionne.", inline=False)
        embed.add_field(name="!status", value="Statut du monitoring par blockchain.", inline=False)
        embed.add_field(name="!baseon / !baseoff", value="Active/désactive le monitoring Base.", inline=False)
        embed.add_field(name="!solanaon / !solanaoff", value="Active/désactive le monitoring Solana.", inline=False)
        embed.add_field(name="!lasttoken", value="Affiche le dernier token détecté (Base/Solana).", inline=False)
        embed.add_field(name="!lasttrump", value="Affiche le dernier post de Trump sur Truth Social.", inline=False)
        embed.add_field(name="!clankeron / !clankeroff", value="Active/désactive le monitoring Clanker.", inline=False)
        embed.add_field(name="!lastclanker", value="Affiche le dernier token déployé sur Clanker.", inline=False)
        embed.add_field(name="!volume <contract>", value="Affiche le volume du token sur 24h, 6h, 1h, 5min.", inline=False)
        embed.add_field(name="!setvolume <usd>", value="Définit le seuil global d'alerte volume (5min).", inline=False)
        embed.add_field(name="!banfid <fid>", value="Bannit un FID pour ne plus recevoir ses alertes de déploiement.", inline=False)
        embed.add_field(name="!unbanfid <fid>", value="Débannit un FID pour recevoir à nouveau ses alertes.", inline=False)
        embed.add_field(name="!listbanned", value="Affiche la liste des FIDs bannis.", inline=False)
        embed.add_field(name="!importbanlist", value="Importe des listes de FIDs à bannir depuis des fichiers texte.", inline=False)
        embed.add_field(name="!exportbanlist", value="Exporte la liste des FIDs bannis dans un fichier.", inline=False)
        embed.add_field(name="!fidcheck <contract>", value="Vérifie le FID associé à un contrat Clanker.", inline=False)
        embed.add_field(name="!spamcheck", value="Liste les FIDs ayant déployé plus d'un token dans les dernières 24h.", inline=False)
        embed.add_field(name="!whitelist <fid>", value="Ajoute un FID à la whitelist (alertes premium).", inline=False)
        embed.add_field(name="!removewhitelist <fid>", value="Retire un FID de la whitelist.", inline=False)
        embed.add_field(name="!checkwhitelist", value="Affiche la liste des FIDs whitelistés.", inline=False)
        embed.add_field(name="!importwhitelist", value="Importe des listes de FIDs depuis des fichiers texte.", inline=False)
        embed.add_field(name="!exportwhitelist", value="Exporte la liste des FIDs whitelistés dans un fichier.", inline=False)
        embed.add_field(name="!importfollowing <username> <limit>", value="Importe les FIDs des comptes suivis par un utilisateur Warpcast.", inline=False)
        await ctx.send(embed=embed)

class ClankerMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen_tokens: Set[str] = self._load_seen_tokens()
        self.channel = None
        self.is_active = True
        self.premium_only = False
        self.bankr_enabled = True
        self.img_required = False  # Nouvelle variable pour le filtre d'image
        self.tracked_clanker_tokens = {}
        self.default_volume_threshold = 5000
        
        # Charger les FIDs bannis et whitelistés au démarrage
        logger.info("Loading banned and whitelisted FIDs...")
        self.banned_fids: Set[str] = self._load_banned_fids()
        self.whitelisted_fids: Set[str] = self._load_whitelisted_fids()
        logger.info(f"Loaded {len(self.banned_fids)} banned FIDs and {len(self.whitelisted_fids)} whitelisted FIDs")

    def _load_seen_tokens(self) -> Set[str]:
        """Load previously seen Clanker token addresses from file."""
        try:
            if os.path.exists(SEEN_CLANKER_TOKENS_FILE):
                with open(SEEN_CLANKER_TOKENS_FILE, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Error loading seen Clanker tokens: {e}")
            return set()

    def _save_seen_tokens(self):
        """Save seen Clanker token addresses to file."""
        try:
            with open(SEEN_CLANKER_TOKENS_FILE, 'w') as f:
                json.dump(list(self.seen_tokens), f)
        except Exception as e:
            logger.error(f"Error saving seen Clanker tokens: {e}")

    def _load_banned_fids(self) -> Set[str]:
        """Load banned FIDs from file."""
        try:
            if os.path.exists(BANNED_FIDS_FILE):
                with open(BANNED_FIDS_FILE, 'r') as f:
                    banned_fids = set(json.load(f))
                    logger.info(f"Successfully loaded {len(banned_fids)} banned FIDs from {BANNED_FIDS_FILE}")
                    return banned_fids
            # Si le fichier n'existe pas, le créer avec un ensemble vide
            logger.info(f"Creating new {BANNED_FIDS_FILE} file")
            self._save_banned_fids(set())
            return set()
        except Exception as e:
            logger.error(f"Error loading banned FIDs: {e}")
            return set()

    def _save_banned_fids(self, fids: Set[str] = None):
        """Save banned FIDs to file."""
        try:
            # Si aucun ensemble n'est fourni, utiliser l'ensemble actuel
            fids_to_save = list(fids if fids is not None else self.banned_fids)
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(BANNED_FIDS_FILE) or '.', exist_ok=True)
            with open(BANNED_FIDS_FILE, 'w') as f:
                json.dump(fids_to_save, f, indent=2)
            logger.info(f"Successfully saved {len(fids_to_save)} banned FIDs to {BANNED_FIDS_FILE}")
        except Exception as e:
            logger.error(f"Error saving banned FIDs: {e}")

    def _load_whitelisted_fids(self) -> Set[str]:
        """Load whitelisted FIDs from file."""
        try:
            if os.path.exists(WHITELISTED_FIDS_FILE):
                with open(WHITELISTED_FIDS_FILE, 'r') as f:
                    whitelisted_fids = set(json.load(f))
                    logger.info(f"Successfully loaded {len(whitelisted_fids)} whitelisted FIDs from {WHITELISTED_FIDS_FILE}")
                    return whitelisted_fids
            # Si le fichier n'existe pas, le créer avec un ensemble vide
            logger.info(f"Creating new {WHITELISTED_FIDS_FILE} file")
            self._save_whitelisted_fids(set())
            return set()
        except Exception as e:
            logger.error(f"Error loading whitelisted FIDs: {e}")
            return set()

    def _save_whitelisted_fids(self, fids: Set[str] = None):
        """Save whitelisted FIDs to file."""
        try:
            # Si aucun ensemble n'est fourni, utiliser l'ensemble actuel
            fids_to_save = list(fids if fids is not None else self.whitelisted_fids)
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(WHITELISTED_FIDS_FILE) or '.', exist_ok=True)
            with open(WHITELISTED_FIDS_FILE, 'w') as f:
                json.dump(fids_to_save, f, indent=2)
            logger.info(f"Successfully saved {len(fids_to_save)} whitelisted FIDs to {WHITELISTED_FIDS_FILE}")
        except Exception as e:
            logger.error(f"Error saving whitelisted FIDs: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def banfid(self, ctx, fid: str):
        """Bannir un FID pour ne plus recevoir ses alertes de déploiement."""
        if not fid.isdigit():
            await ctx.send("❌ Le FID doit être un nombre.")
            return
            
        self.banned_fids.add(fid)
        self._save_banned_fids()  # Sauvegarder immédiatement après modification
        await ctx.send(f"✅ FID {fid} banni avec succès. Vous ne recevrez plus d'alertes de ce compte.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unbanfid(self, ctx, fid: str):
        """Débannir un FID pour recevoir à nouveau ses alertes de déploiement."""
        if fid in self.banned_fids:
            self.banned_fids.remove(fid)
            self._save_banned_fids()  # Sauvegarder immédiatement après modification
            await ctx.send(f"✅ FID {fid} débanni avec succès. Vous recevrez à nouveau les alertes de ce compte.")
        else:
            await ctx.send("❌ Ce FID n'est pas banni.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def listbanned(self, ctx):
        """Afficher la liste des FIDs bannis."""
        if not self.banned_fids:
            await ctx.send("Aucun FID n'est actuellement banni.")
            return
            
        embed = discord.Embed(
            title="Liste des FIDs bannis",
            description="\n".join(f"• FID: {fid}" for fid in sorted(self.banned_fids)),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spamcheck(self, ctx):
        """Analyse les déploiements Clanker des dernières 24h pour identifier les spammeurs."""
        try:
            # Message initial
            status_msg = await ctx.send("🔍 Analyse des déploiements Clanker des dernières 24h en cours...")

            # Récupérer tous les tokens des dernières 24h
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{CLANKER_API_URL}/tokens", params={"limit": 1000})
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, dict) or "data" not in data:
                    await status_msg.edit(content="❌ Format de réponse invalide de l'API Clanker")
                    return

                tokens = data["data"]
                
                # Filtrer les tokens des dernières 24h
                now = datetime.now(timezone.utc)
                cutoff = now - timedelta(hours=24)
                
                # Compter les déploiements par FID
                fid_counts = {}
                fid_tokens = {}  # Pour stocker les détails des tokens par FID
                
                for token in tokens:
                    # Vérifier la date de création
                    created_at_str = token.get('created_at')
                    if not created_at_str:
                        continue
                        
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_at < cutoff:
                            continue
                            
                        fid = str(token.get('requestor_fid'))
                        if not fid:
                            continue
                            
                        if fid not in fid_counts:
                            fid_counts[fid] = 0
                            fid_tokens[fid] = []
                            
                        fid_counts[fid] += 1
                        fid_tokens[fid].append({
                            'name': token.get('name', 'Unknown'),
                            'symbol': token.get('symbol', 'Unknown'),
                            'contract': token.get('contract_address', 'Unknown')
                        })
                            
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error parsing date: {e}")
                        continue

                # Filtrer les FIDs avec plus d'un déploiement
                spammers = {fid: count for fid, count in fid_counts.items() if count > 1}
                
                if not spammers:
                    await status_msg.edit(content="✅ Aucun spammeur détecté dans les dernières 24h!")
                    return

                # Créer l'embed avec les résultats
                embed = discord.Embed(
                    title="🚨 Spammeurs de Clanker (24h)",
                    description="Liste des FIDs ayant déployé plus d'un token dans les dernières 24h",
                    color=discord.Color.red(),
                    timestamp=now
                )

                # Trier par nombre de déploiements (du plus grand au plus petit)
                sorted_spammers = sorted(spammers.items(), key=lambda x: x[1], reverse=True)

                for fid, count in sorted_spammers:
                    # Créer la liste des tokens pour ce FID
                    token_list = []
                    for token in fid_tokens[fid]:
                        token_list.append(f"• {token['name']} ({token['symbol']})")
                        if len(token_list[-1]) > 50:  # Tronquer si trop long
                            token_list[-1] = token_list[-1][:47] + "..."

                    tokens_text = "\n".join(token_list)
                    if len(tokens_text) > 1024:  # Limite Discord pour un field
                        tokens_text = tokens_text[:1021] + "..."

                    embed.add_field(
                        name=f"FID: {fid} ({count} tokens)",
                        value=tokens_text,
                        inline=False
                    )

                # Ajouter un footer avec des instructions
                embed.set_footer(text="Utilisez !banfid <fid> pour bannir un FID spécifique")

                await status_msg.delete()
                await ctx.send(embed=embed)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during spam check: {e}")
            await status_msg.edit(content="❌ Erreur lors de la requête à l'API Clanker")
        except Exception as e:
            logger.error(f"Error during spam check: {e}")
            await status_msg.edit(content="❌ Une erreur est survenue lors de la vérification des spammeurs")

    @commands.command()
    async def fidcheck(self, ctx, contract_address: str):
        """Vérifie le FID associé à un contrat Clanker."""
        try:
            # Envoyer un message initial
            status_msg = await ctx.send("🔍 Recherche du FID...")

            # Faire la requête à l'API Clanker
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{CLANKER_API_URL}/tokens", params={"contract": contract_address})
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, dict) or "data" not in data or not data["data"]:
                    await status_msg.edit(content=f"❌ Aucun token trouvé pour le contrat {contract_address}")
                    return

                token = data["data"][0]  # Prendre le premier résultat
                social_context = token.get('social_context', {})
                
                # Log pour le débogage
                logger.info(f"[FIDCHECK] Token data: {token}")
                logger.info(f"[FIDCHECK] Social context: {social_context}")

                # Créer un embed avec les informations
                embed = discord.Embed(
                    title="🔍 Informations FID",
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name="Contract",
                    value=f"`{contract_address}`",
                    inline=False
                )

                # Ajouter le FID s'il existe
                fid = token.get('requestor_fid')
                if fid:
                    embed.add_field(
                        name="FID",
                        value=str(fid),
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="FID",
                        value="Non trouvé",
                        inline=True
                    )

                # Ajouter d'autres informations utiles
                platform = social_context.get('platform', 'Unknown')
                interface = social_context.get('interface', 'Unknown')
                username = social_context.get('username')

                embed.add_field(
                    name="Plateforme",
                    value=platform,
                    inline=True
                )

                embed.add_field(
                    name="Interface",
                    value=interface,
                    inline=True
                )

                if username:
                    embed.add_field(
                        name="Username",
                        value=username,
                        inline=True
                    )

                # Supprimer le message de statut et envoyer l'embed
                await status_msg.delete()
                await ctx.send(embed=embed)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during FID check: {e}")
            await status_msg.edit(content="❌ Erreur lors de la requête à l'API Clanker")
        except Exception as e:
            logger.error(f"Error during FID check: {e}")
            await status_msg.edit(content="❌ Une erreur est survenue lors de la vérification du FID")

    @commands.command()
    async def clankeron(self, ctx):
        """Activer le monitoring pour Clanker"""
        self.is_active = True
        await ctx.send("✅ Monitoring Clanker activé")

    @commands.command()
    async def clankeroff(self, ctx):
        """Désactiver le monitoring pour Clanker"""
        self.is_active = False
        await ctx.send("❌ Monitoring Clanker désactivé")

    @commands.command()
    async def lastclanker(self, ctx):
        """Fetch and display the latest token from Clanker"""
        try:
            # Send initial message
            status_msg = await ctx.send("🔍 Recherche du dernier token Clanker...")
            
            # Fetch latest Clanker deployments with timeout and SSL verification
            async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
                try:
                    response = await client.get(f"{CLANKER_API_URL}/tokens", params={"page": 1, "sort": "desc"})
                    response.raise_for_status()
                    data = response.json()

                    if not isinstance(data, dict) or "data" not in data:
                        await status_msg.edit(content="❌ Format de réponse invalide de l'API Clanker.")
                        return

                    tokens = data["data"]
                    if tokens:
                        # Get the first (latest) token
                        latest_token = tokens[0]
                        # Delete the status message
                        await status_msg.delete()
                        # Send token notification
                        await self._send_clanker_notification(latest_token, ctx.channel)
                    else:
                        await status_msg.edit(content="❌ Aucun token récent trouvé sur Clanker.")

                except httpx.ConnectError:
                    await status_msg.edit(content="❌ Impossible de se connecter à l'API Clanker. Veuillez réessayer plus tard.")
                except httpx.TimeoutException:
                    await status_msg.edit(content="❌ Délai d'attente dépassé lors de la connexion à l'API Clanker.")
                except httpx.HTTPStatusError as e:
                    await status_msg.edit(content=f"❌ Erreur lors de la requête à l'API Clanker: {e.response.status_code}")
                except json.JSONDecodeError:
                    await status_msg.edit(content="❌ Réponse invalide reçue de l'API Clanker.")

        except Exception as e:
            logger.error(f"Error fetching latest Clanker token: {e}")
            if status_msg:
                await status_msg.edit(content="❌ Erreur lors de la recherche du dernier token Clanker.")
            else:
                await ctx.send("❌ Erreur lors de la recherche du dernier token Clanker.")

    async def _send_clanker_notification(self, token_data: Dict, channel: discord.TextChannel):
        """Send a notification for a new Clanker token."""
        try:
            # Logging des données sociales pour débogage
            social_context = token_data.get('social_context', {})
            logger.info(f"[DEBUG] Social Context Data: {social_context}")
            logger.info(f"[DEBUG] Platform: {social_context.get('platform')}")
            logger.info(f"[DEBUG] Interface: {social_context.get('interface')}")
            logger.info(f"[DEBUG] Username: {social_context.get('username')}")
            logger.info(f"[DEBUG] FID: {token_data.get('requestor_fid')}")

            # Vérifier si le FID est banni
            fid = str(token_data.get('requestor_fid', ''))
            if fid and fid in self.banned_fids:
                logger.info(f"Skipping notification for banned FID: {fid}")
                return

            # Vérifier si le FID est whitelisté
            is_premium = fid and fid in self.whitelisted_fids

            # Si le mode premium est activé et que le token n'est pas premium, on ne l'affiche pas
            if self.premium_only and not is_premium:
                logger.info(f"Skipping non-premium token in premium-only mode: {token_data.get('name')}")
                return

            # Filtrage selon la méthode de déploiement
            platform = social_context.get('platform', 'Unknown')
            interface = social_context.get('interface', 'Unknown')
            username = social_context.get('username')

            # Vérifier si c'est un token Bankr et si les alertes Bankr sont désactivées
            if platform == "Unknown" and interface == "Bankr" and not self.bankr_enabled:
                logger.info(f"Skipping Bankr token as Bankr alerts are disabled: {token_data.get('name')}")
                return

            # Vérifier si le filtre d'image est activé et si le token n'a pas d'image
            # On ignore le filtre d'image si le token est premium
            if self.img_required and not is_premium and not token_data.get('img_url'):
                logger.info(f"Skipping token without image as image filter is enabled: {token_data.get('name')}")
                return

            # On ne garde que farcaster (clanker) OU Unknown (Bankr)
            if not (
                (platform.lower() == "farcaster") or
                (platform == "Unknown" and interface == "Bankr")
            ):
                return  # On ne notifie pas

            cast_hash = token_data.get('cast_hash')
            contract_address = token_data.get('contract_address')
            tweet_link = None
            clanker_link = f"https://www.clanker.world/clanker/{contract_address}" if contract_address else None

            # Pour Farcaster, générer le lien Warpcast si username et cast_hash sont présents
            if platform.lower() == "farcaster":
                if username and cast_hash:
                    tweet_link = f"https://warpcast.com/{username}/{cast_hash}"
                elif cast_hash:
                    tweet_link = cast_hash
                else:
                    tweet_link = "(Aucun cast_hash disponible)"
            elif cast_hash:
                tweet_link = cast_hash

            # Filtrer pour ne garder que les alertes avec un lien Twitter (Bankr) ou un cast_hash (Farcaster)
            if platform.lower() == "farcaster":
                if not tweet_link:
                    return  # On ne notifie pas si pas de cast_hash pour Farcaster
            else:
                if not (tweet_link and tweet_link.startswith("https://twitter.com/")):
                    return  # On ne notifie pas si pas de lien Twitter pour Bankr

            embed = discord.Embed(
                title="🥇 Clanker Premium Lancé" if is_premium else "🆕 Nouveau Token Clanker",
                description=token_data.get('metadata', {}).get('description', 'Un nouveau token a été déployé sur Clanker!'),
                color=discord.Color.gold() if is_premium else discord.Color(0x800080),
                timestamp=datetime.now(timezone.utc)
            )

            # Add token information
            embed.add_field(
                name="Nom du Token",
                value=token_data.get('name', 'Unknown'),
                inline=True
            )
            
            embed.add_field(
                name="Symbole",
                value=token_data.get('symbol', 'Unknown'),
                inline=True
            )

            # Add FID if available and create Blacklist button
            if fid:
                embed.add_field(
                    name="FID",
                    value=fid + (" 🥇" if is_premium else ""),
                    inline=True
                )
                # Create button view
                view = discord.ui.View()
                blacklist_button = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="Blacklist",
                    custom_id=f"blacklist_{fid}"
                )
                view.add_item(blacklist_button)
                # Ajout du bouton Remove Whitelist si premium
                if is_premium:
                    remove_whitelist_button = discord.ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label="Remove Whitelist",
                        custom_id=f"removewhitelist_{fid}"
                    )
                    view.add_item(remove_whitelist_button)
            else:
                view = None

            embed.add_field(
                name="Contract",
                value=f"`{contract_address or 'Unknown'}`",
                inline=False
            )

            # Add pool information if available
            if token_data.get('pool_address'):
                embed.add_field(
                    name="Pool Address",
                    value=f"`{token_data['pool_address']}`",
                    inline=False
                )
                # Ajout du bouton Photon
                if view is None:
                    view = discord.ui.View()
                photon_url = f"https://photon-base.tinyastro.io/en/lp/{token_data['pool_address']}"
                photon_button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Voir sur Photon",
                    url=photon_url
                )
                view.add_item(photon_button)

            # Add deployment tweet/cast link
            embed.add_field(
                name="Tweet/Cast de Déploiement",
                value=tweet_link,
                inline=False
            )

            # Ajoute le lien clanker.world si disponible
            if clanker_link:
                embed.add_field(
                    name="Lien Clanker",
                    value=f"[Voir sur Clanker.world]({clanker_link})",
                    inline=False
                )

            # Add token image if available
            if token_data.get('img_url'):
                embed.set_thumbnail(url=token_data['img_url'])

            # Add social context if available
            embed.add_field(
                name="Déployé via",
                value=f"{platform} ({interface})",
                inline=True
            )

            # Add username with Warpcast link if available
            if username and platform.lower() == "farcaster":
                embed.add_field(
                    name="Username",
                    value=f"[@{username}](https://warpcast.com/{username})",
                inline=True
                )

            # Add market cap if available
            if market_cap := token_data.get('starting_market_cap'):
                embed.add_field(
                    name="Market Cap Initial",
                    value=f"${market_cap:,.2f}",
                    inline=True
                )

            # Send message with button if FID is available or Photon button exists
            if view:
                await channel.send(embed=embed, view=view)
            else:
                await channel.send(embed=embed)

            logger.info(f"Clanker notification sent for token: {token_data.get('name')}")

            if contract_address:
                # Ajoute le token à la liste de surveillance du volume
                self.tracked_clanker_tokens[contract_address.lower()] = {
                    'first_seen': time.time(),
                    'alerted': False
                }

        except Exception as e:
            logger.error(f"Error sending Clanker notification: {e}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions."""
        if not interaction.data:
            return

        try:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id.startswith("blacklist_"):
                # Extract FID from custom_id
                fid = custom_id.split("_")[1]
                
                # Check if user has admin permissions
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette fonction.", ephemeral=True)
                    return

                # Check if FID is already banned
                if fid in self.banned_fids:
                    await interaction.response.send_message(f"ℹ️ Le FID {fid} est déjà banni.", ephemeral=True)
                    return

                # Check if FID is whitelisted
                if fid in self.whitelisted_fids:
                    await interaction.response.send_message(f"⚠️ Le FID {fid} est whitelisté et ne peut pas être banni.", ephemeral=True)
                    return

                # Add FID to banlist
                self.banned_fids.add(fid)
                self._save_banned_fids()
                
                await interaction.response.send_message(f"✅ FID {fid} ajouté à la banlist avec succès.", ephemeral=True)
                logger.info(f"FID {fid} banned via button interaction by {interaction.user}")
            elif custom_id.startswith("removewhitelist_"):
                fid = custom_id.split("_")[1]
                # Check if user has admin permissions
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette fonction.", ephemeral=True)
                    return
                if fid not in self.whitelisted_fids:
                    await interaction.response.send_message(f"❌ Le FID {fid} n'est pas dans la whitelist.", ephemeral=True)
                    return
                self.whitelisted_fids.remove(fid)
                self._save_whitelisted_fids()
                await interaction.response.send_message(f"✅ FID {fid} retiré de la whitelist avec succès.", ephemeral=True)
                logger.info(f"FID {fid} removed from whitelist via button interaction by {interaction.user}")

        except Exception as e:
            logger.error(f"Error handling button interaction: {e}")
            await interaction.response.send_message("❌ Une erreur est survenue lors du traitement de votre demande.", ephemeral=True)

    @commands.command()
    async def setvolume(self, ctx, volume_usd: float):
        """Définit le seuil d'alerte volume (en USD) pour tous les tokens Clanker."""
        if volume_usd <= 0:
            await ctx.send("❌ Le seuil doit être strictement positif.")
            return
        self.default_volume_threshold = volume_usd
        await ctx.send(f"✅ Seuil d'alerte global défini à {volume_usd} USD sur 5 minutes pour tous les tokens.")

    @tasks.loop(seconds=60)
    async def monitor_clanker_volumes(self):
        """Surveille le volume sur 5 minutes des tokens Clanker détectés."""
        if not self.is_active or not self.channel:
            return
        to_remove = []
        for contract_address, info in list(self.tracked_clanker_tokens.items()):
            if info.get('alerted'):
                continue  # Déjà alerté
            # Appel Dexscreener
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url)
                    data = resp.json()
                    pairs = data.get('pairs', [])
                    if not pairs:
                        continue
                    # On prend le premier pair trouvé
                    pair = pairs[0]
                    volume_5m = float(pair.get('volume', {}).get('m5', 0))
                    symbol = pair.get('baseToken', {}).get('symbol', contract_address)
                    name = pair.get('baseToken', {}).get('name', contract_address)
                    threshold = self.default_volume_threshold
                    if volume_5m >= threshold:
                        # Envoie une alerte Discord
                        embed = discord.Embed(
                            title="🚨 Volume Clanker élevé!",
                            description=f"Le token {name} ({symbol}) a dépassé {threshold}$ de volume sur 5 minutes!",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.add_field(name="Contract", value=f"`{contract_address}`", inline=False)
                        embed.add_field(name="Volume (5min)", value=f"${volume_5m:,.2f}", inline=False)
                        embed.add_field(name="Dexscreener", value=f"[Voir]({pair.get('url', 'https://dexscreener.com')})", inline=False)
                        # Ajout du bouton Photon si pool address
                        view = None
                        pool_address = pair.get('pairAddress') or pair.get('poolAddress') or pair.get('liquidity', {}).get('address')
                        if pool_address:
                            photon_url = f"https://photon-base.tinyastro.io/en/lp/{pool_address}"
                            view = discord.ui.View()
                            photon_button = discord.ui.Button(
                                style=discord.ButtonStyle.primary,
                                label="Voir sur Photon",
                                url=photon_url
                            )
                            view.add_item(photon_button)
                        if view:
                            await self.channel.send(embed=embed, view=view)
                        else:
                            await self.channel.send(embed=embed)
                        self.tracked_clanker_tokens[contract_address]['alerted'] = True
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du volume Dexscreener pour {contract_address}: {e}")
        # Nettoyage optionnel: on peut retirer les tokens alertés depuis longtemps
        for contract_address, info in list(self.tracked_clanker_tokens.items()):
            if info.get('alerted') and (time.time() - info['first_seen'] > 3600):
                to_remove.append(contract_address)
        for contract_address in to_remove:
            del self.tracked_clanker_tokens[contract_address]

    @monitor_clanker_volumes.before_loop
    async def before_monitor_clanker_volumes(self):
        await self.bot.wait_until_ready()
        if not self.channel:
            self.channel = self.bot.get_channel(CHANNEL_ID)

    @tasks.loop(seconds=POLL_INTERVAL)
    async def monitor_clanker(self):
        """Monitor for new Clanker token deployments."""
        if not self.is_active:
            return

        try:
            if not self.channel:
                self.channel = self.bot.get_channel(CHANNEL_ID)
                if not self.channel:
                    logger.error("Could not find channel for Clanker notifications")
                    return

            # Fetch latest Clanker deployments with timeout and SSL verification
            async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
                try:
                    response = await client.get(f"{CLANKER_API_URL}/tokens", params={"page": 1, "sort": "desc"})
                    response.raise_for_status()
                    data = response.json()

                    if not isinstance(data, dict) or "data" not in data:
                        logger.error("Invalid response format from Clanker API")
                        return

                    tokens = data["data"]
                    for token in tokens:
                        # LOG DEBUG pour chaque token reçu
                        social_context = token.get('social_context', {})
                        logger.info(f"[DEBUG CLANKER] contract_address={token.get('contract_address')}, cast_hash={token.get('cast_hash')}, username={social_context.get('username')}, platform={social_context.get('platform')}, interface={social_context.get('interface')}, token={token}")
                        contract_address = token.get('contract_address')
                        if contract_address and contract_address not in self.seen_tokens:
                            await self._send_clanker_notification(token, self.channel)
                            self.seen_tokens.add(contract_address)
                            self._save_seen_tokens()

                except httpx.ConnectError as e:
                    logger.error(f"Connection error to Clanker API: {e}")
                except httpx.TimeoutException as e:
                    logger.error(f"Timeout while connecting to Clanker API: {e}")
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error from Clanker API: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from Clanker API: {e}")

        except Exception as e:
            logger.error(f"Error monitoring Clanker: {e}")

    @monitor_clanker.before_loop
    async def before_monitor_clanker(self):
        """Wait for bot to be ready before starting the Clanker monitoring loop."""
        await self.bot.wait_until_ready()

    @commands.command()
    async def volume(self, ctx, contract: str):
        """Affiche le volume du token sur 24h, 6h, 1h et 5min via Dexscreener."""
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                data = resp.json()
                pairs = data.get('pairs', [])
                if not pairs:
                    await ctx.send("❌ Aucun pair trouvé pour ce contrat sur Dexscreener.")
                    return
                pair = pairs[0]
                volume = pair.get('volume', {})
                symbol = pair.get('baseToken', {}).get('symbol', contract)
                name = pair.get('baseToken', {}).get('name', contract)
                embed = discord.Embed(
                    title=f"Volumes pour {name} ({symbol})",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Contract", value=f"`{contract}`", inline=False)
                embed.add_field(name="Volume 24h", value=f"${float(volume.get('h24', 0)):,}", inline=True)
                embed.add_field(name="Volume 6h", value=f"${float(volume.get('h6', 0)):,}", inline=True)
                embed.add_field(name="Volume 1h", value=f"${float(volume.get('h1', 0)):,}", inline=True)
                embed.add_field(name="Volume 5min", value=f"${float(volume.get('m5', 0)):,}", inline=True)
                embed.add_field(name="Dexscreener", value=f"[Voir]({pair.get('url', 'https://dexscreener.com')})", inline=False)
                await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du volume Dexscreener pour {contract}: {e}")
            await ctx.send("❌ Erreur lors de la récupération du volume Dexscreener.")

    @commands.command()
    async def testvolumealert(self, ctx):
        """Simule une alerte de volume Clanker dépassant 5000 USD sur 5 minutes."""
        contract_address = "0xFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE"
        name = "TokenTest"
        symbol = "TST"
        volume_5m = 12345.67
        dexscreener_url = f"https://dexscreener.com/base/{contract_address}"
        embed = discord.Embed(
            title="🚨 Volume Clanker élevé!",
            description=f"Le token {name} ({symbol}) a dépassé 5000$ de volume sur 5 minutes!",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Contract", value=f"`{contract_address}`", inline=False)
        embed.add_field(name="Volume (5min)", value=f"${volume_5m:,.2f}", inline=False)
        embed.add_field(name="Dexscreener", value=f"[Voir]({dexscreener_url})", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def checkwhitelist(self, ctx):
        """Afficher la liste des FIDs whitelistés."""
        if not self.whitelisted_fids:
            await ctx.send("Aucun FID n'est actuellement dans la whitelist.")
            return
            
        embed = discord.Embed(
            title="🥇 Liste des FIDs Premium",
            description="\n".join(f"• FID: {fid}" for fid in sorted(self.whitelisted_fids)),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx, fid: str):
        """Ajouter un FID à la whitelist."""
        if not fid.isdigit():
            await ctx.send("❌ Le FID doit être un nombre.")
            return

        if fid in self.banned_fids:
            await ctx.send("❌ Ce FID est banni. Veuillez d'abord le débannir avec !unbanfid.")
            return

        self.whitelisted_fids.add(fid)
        self._save_whitelisted_fids()  # Sauvegarder immédiatement après modification
        await ctx.send(f"✅ FID {fid} ajouté à la whitelist avec succès.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removewhitelist(self, ctx, fid: str):
        """Retirer un FID de la whitelist."""
        if fid in self.whitelisted_fids:
            self.whitelisted_fids.remove(fid)
            self._save_whitelisted_fids()  # Sauvegarder immédiatement après modification
            await ctx.send(f"✅ FID {fid} retiré de la whitelist avec succès.")
        else:
            await ctx.send("❌ Ce FID n'est pas dans la whitelist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def importfollowing(self, ctx, username: str, limit: int = 100):
        """Importe les FIDs des comptes suivis par un utilisateur Warpcast."""
        try:
            if limit <= 0:
                await ctx.send("❌ La limite doit être un nombre positif.")
                return
                
            status_msg = await ctx.send(f"🔍 Recherche des comptes suivis par @{username}...")

            # Première requête pour obtenir le FID de l'utilisateur cible
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{WARPCAST_API_URL}/user-search",
                    params={"q": username}
                )
                response.raise_for_status()
                data = response.json()

                if not data.get("result", {}).get("users"):
                    await status_msg.edit(content=f"❌ Utilisateur @{username} non trouvé sur Warpcast.")
                    return

                target_user = data["result"]["users"][0]
                target_fid = target_user.get("fid")

                if not target_fid:
                    await status_msg.edit(content=f"❌ Impossible de trouver le FID de @{username}.")
                    return

                # Variables pour la pagination
                following = []
                cursor = None
                total_fetched = 0

                # Boucle de pagination pour récupérer tous les follows
                while True:
                    params = {"fid": target_fid, "limit": 100}  # Limite max par requête
                    if cursor:
                        params["cursor"] = cursor

                    await status_msg.edit(content=f"🔍 Récupération des comptes suivis... ({total_fetched} trouvés)")
                    
                    response = await client.get(
                        f"{WARPCAST_API_URL}/following",
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()

                    if "result" not in data:
                        await status_msg.edit(content="❌ Erreur lors de la récupération des comptes suivis.")
                        return

                    batch = data["result"].get("users", [])
                    following.extend(batch)
                    total_fetched += len(batch)

                    # Vérifier s'il y a plus de résultats
                    cursor = data["result"].get("next", {}).get("cursor")
                    if not cursor or total_fetched >= limit:
                        break

                if not following:
                    await status_msg.edit(content=f"❌ @{username} ne suit aucun compte.")
                    return

                # Limiter au nombre demandé
                following = following[:limit]
                
                # Créer un embed avec la liste des comptes trouvés
                embed = discord.Embed(
                    title=f"👥 Comptes suivis par @{username}",
                    description=f"Voici les {len(following)} premiers FIDs des comptes suivis (sur un total de {total_fetched}). Utilisez !whitelist <fid> pour les ajouter à la whitelist.",
                    color=discord.Color.blue()
                )

                # Grouper les comptes par paquets de 15 pour respecter la limite de Discord
                chunks = [following[i:i + 15] for i in range(0, len(following), 15)]
                
                for i, chunk in enumerate(chunks[:15]):  # Maximum 15 champs pour garder de la place pour le résumé
                    field_text = ""
                    for user in chunk:
                        fid = user.get("fid")
                        display_name = user.get("displayName", "Unknown")
                        username = user.get("username", "Unknown")
                        
                        # Marquer si déjà whitelisté
                        status = "🥇" if str(fid) in self.whitelisted_fids else "⭐"
                        field_text += f"{status} **FID:** {fid} - @{username} ({display_name})\n"

                    embed.add_field(
                        name=f"Liste {i+1}/{min(len(chunks), 15)}",
                        value=field_text or "Aucun compte trouvé",
                        inline=False
                    )

                # Ajouter un résumé
                already_whitelisted = sum(1 for user in following if str(user.get("fid", "")) in self.whitelisted_fids)

                embed.add_field(
                    name="Résumé",
                    value=f"Affichés: {len(following)} comptes\nTotal suivis: {total_fetched}\nDéjà whitelistés: {already_whitelisted}\nNon whitelistés: {len(following) - already_whitelisted}",
                    inline=False
                )

                embed.set_footer(text="🥇 = Déjà whitelisté | ⭐ = Non whitelisté | Utilisez !importfollowing <username> <limit> pour voir plus de résultats")

                await status_msg.delete()
                await ctx.send(embed=embed)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during following import: {e}")
            await status_msg.edit(content="❌ Erreur lors de la connexion à l'API Warpcast")
        except Exception as e:
            logger.error(f"Error during following import: {e}")
            await status_msg.edit(content="❌ Une erreur est survenue lors de l'importation")

    @commands.command(name='exportwhitelist')
    @commands.has_permissions(administrator=True)
    async def export_whitelist(self, ctx):
        """Exporte le fichier de whitelist"""
        try:
            if os.path.exists(WHITELISTED_FIDS_FILE):
                await ctx.send(file=discord.File(WHITELISTED_FIDS_FILE))
            else:
                await ctx.send("❌ Le fichier de whitelist n'existe pas.")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'export: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def importwhitelist(self, ctx):
        """Importe des listes de FIDs depuis des fichiers texte (.txt) ou JSON (.json) attachés au message.
        Format .txt : un FID par ligne
        Format .json : liste de FIDs exportée par !exportwhitelist"""
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez attacher un ou plusieurs fichiers (.txt ou .json) contenant les FIDs.")
            return

        # Vérifier que tous les fichiers sont au format accepté
        invalid_files = [att.filename for att in ctx.message.attachments 
                        if not (att.filename.endswith('.txt') or att.filename.endswith('.json'))]
        if invalid_files:
            await ctx.send(f"❌ Les fichiers suivants ne sont pas au format .txt ou .json : {', '.join(invalid_files)}")
            return

        status_msg = await ctx.send(f"📥 Traitement de {len(ctx.message.attachments)} fichier(s) en cours...")

        try:
            # Statistiques globales
            total_stats = {
                'added': set(),
                'invalid': [],
                'banned': [],
                'already_whitelisted': []
            }
            
            # Statistiques par fichier
            file_stats = {}

            # Traiter chaque fichier
            for attachment in ctx.message.attachments:
                # Statistiques pour ce fichier
                file_stats[attachment.filename] = {
                    'added': set(),
                    'invalid': [],
                    'banned': [],
                    'already_whitelisted': []
                }

                # Télécharger et lire le contenu du fichier
                content = await attachment.read()
                content = content.decode('utf-8')
                
                # Liste des FIDs à traiter
                fids_to_process = []
                
                # Traiter selon le format du fichier
                if attachment.filename.endswith('.json'):
                    try:
                        json_data = json.loads(content)
                        if isinstance(json_data, list):
                            fids_to_process = [str(fid).strip() for fid in json_data]
                        else:
                            file_stats[attachment.filename]['invalid'].append("Format JSON invalide")
                            total_stats['invalid'].append("Format JSON invalide")
                            continue
                    except json.JSONDecodeError:
                        file_stats[attachment.filename]['invalid'].append("JSON invalide")
                        total_stats['invalid'].append("JSON invalide")
                        continue
                else:  # .txt
                    fids_to_process = [line.strip() for line in content.split('\n') if line.strip()]

                # Traiter chaque FID
                for fid in fids_to_process:
                    if not fid:  # Ignorer les lignes vides
                        continue
                        
                    if not str(fid).isdigit():
                        file_stats[attachment.filename]['invalid'].append(fid)
                        total_stats['invalid'].append(fid)
                        continue
                        
                    if fid in self.banned_fids:
                        file_stats[attachment.filename]['banned'].append(fid)
                        total_stats['banned'].append(fid)
                        continue
                        
                    if fid in self.whitelisted_fids:
                        file_stats[attachment.filename]['already_whitelisted'].append(fid)
                        total_stats['already_whitelisted'].append(fid)
                        continue
                        
                    file_stats[attachment.filename]['added'].add(fid)
                    total_stats['added'].add(fid)

            # Ajouter tous les nouveaux FIDs à la whitelist
            self.whitelisted_fids.update(total_stats['added'])
            self._save_whitelisted_fids()

            # Créer un embed avec le résumé global
            embed = discord.Embed(
                title="📊 Résultat de l'importation multiple",
                description=f"Traitement de {len(ctx.message.attachments)} fichier(s) terminé",
                color=discord.Color.green() if total_stats['added'] else discord.Color.orange()
            )

            # Résumé global
            embed.add_field(
                name="✅ Total FIDs ajoutés",
                value=f"{len(total_stats['added'])} FIDs ajoutés à la whitelist",
                inline=False
            )

            if total_stats['already_whitelisted']:
                embed.add_field(
                    name="ℹ️ Total déjà whitelistés",
                    value=f"{len(total_stats['already_whitelisted'])} FIDs déjà dans la whitelist",
                    inline=False
                )

            if total_stats['banned']:
                embed.add_field(
                    name="⚠️ Total FIDs bannis (ignorés)",
                    value=f"{len(total_stats['banned'])} FIDs sont bannis et n'ont pas été ajoutés",
                    inline=False
                )

            if total_stats['invalid']:
                invalid_sample = total_stats['invalid'][:5]
                embed.add_field(
                    name="❌ Total FIDs invalides",
                    value=f"{len(total_stats['invalid'])} FIDs invalides trouvés\nExemples: {', '.join(str(x) for x in invalid_sample)}{'...' if len(total_stats['invalid']) > 5 else ''}",
                    inline=False
                )

            # Détails par fichier
            for filename, stats in file_stats.items():
                details = []
                if stats['added']:
                    details.append(f"✅ Ajoutés: {len(stats['added'])}")
                if stats['already_whitelisted']:
                    details.append(f"ℹ️ Déjà whitelistés: {len(stats['already_whitelisted'])}")
                if stats['banned']:
                    details.append(f"⚠️ Bannis: {len(stats['banned'])}")
                if stats['invalid']:
                    details.append(f"❌ Invalides: {len(stats['invalid'])}")
                
                embed.add_field(
                    name=f"📄 {filename}",
                    value="\n".join(details) or "Aucun FID traité",
                    inline=True
                )

            embed.set_footer(text="Utilisez !checkwhitelist pour voir la liste complète")
            
            await status_msg.delete()
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error importing whitelist: {e}")
            await status_msg.edit(content="❌ Une erreur est survenue lors de l'importation des fichiers.")

    @commands.command(name='exportbanlist')
    @commands.has_permissions(administrator=True)
    async def export_banlist(self, ctx):
        """Exporte le fichier de banlist"""
        try:
            if os.path.exists(BANNED_FIDS_FILE):
                await ctx.send(file=discord.File(BANNED_FIDS_FILE))
            else:
                await ctx.send("❌ Le fichier de banlist n'existe pas.")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'export: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def importbanlist(self, ctx):
        """Importe des listes de FIDs à bannir depuis des fichiers texte (.txt) ou JSON (.json) attachés au message.
        Format .txt : un FID par ligne
        Format .json : liste de FIDs exportée par !exportbanlist"""
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez attacher un ou plusieurs fichiers (.txt ou .json) contenant les FIDs.")
            return

        # Vérifier que tous les fichiers sont au format accepté
        invalid_files = [att.filename for att in ctx.message.attachments 
                        if not (att.filename.endswith('.txt') or att.filename.endswith('.json'))]
        if invalid_files:
            await ctx.send(f"❌ Les fichiers suivants ne sont pas au format .txt ou .json : {', '.join(invalid_files)}")
            return

        status_msg = await ctx.send(f"📥 Traitement de {len(ctx.message.attachments)} fichier(s) en cours...")

        try:
            # Statistiques globales
            total_stats = {
                'added': set(),
                'invalid': [],
                'whitelisted': [],
                'already_banned': []
            }
            
            # Statistiques par fichier
            file_stats = {}

            # Traiter chaque fichier
            for attachment in ctx.message.attachments:
                # Statistiques pour ce fichier
                file_stats[attachment.filename] = {
                    'added': set(),
                    'invalid': [],
                    'whitelisted': [],
                    'already_banned': []
                }

                # Télécharger et lire le contenu du fichier
                content = await attachment.read()
                content = content.decode('utf-8')
                
                # Liste des FIDs à traiter
                fids_to_process = []
                
                # Traiter selon le format du fichier
                if attachment.filename.endswith('.json'):
                    try:
                        json_data = json.loads(content)
                        if isinstance(json_data, list):
                            fids_to_process = [str(fid).strip() for fid in json_data]
                        else:
                            file_stats[attachment.filename]['invalid'].append("Format JSON invalide")
                            total_stats['invalid'].append("Format JSON invalide")
                            continue
                    except json.JSONDecodeError:
                        file_stats[attachment.filename]['invalid'].append("JSON invalide")
                        total_stats['invalid'].append("JSON invalide")
                        continue
                else:  # .txt
                    fids_to_process = [line.strip() for line in content.split('\n') if line.strip()]

                # Traiter chaque FID
                for fid in fids_to_process:
                    if not fid:  # Ignorer les lignes vides
                        continue
                    
                    if not str(fid).isdigit():
                        file_stats[attachment.filename]['invalid'].append(fid)
                        total_stats['invalid'].append(fid)
                        continue
                    
                    if fid in self.whitelisted_fids:
                        file_stats[attachment.filename]['whitelisted'].append(fid)
                        total_stats['whitelisted'].append(fid)
                        continue
                    
                    if fid in self.banned_fids:
                        file_stats[attachment.filename]['already_banned'].append(fid)
                        total_stats['already_banned'].append(fid)
                        continue
                    
                    file_stats[attachment.filename]['added'].add(fid)
                    total_stats['added'].add(fid)

            # Ajouter tous les nouveaux FIDs à la banlist
            self.banned_fids.update(total_stats['added'])
            self._save_banned_fids()

            # Créer un embed avec le résumé global
            embed = discord.Embed(
                title="📊 Résultat de l'importation multiple",
                description=f"Traitement de {len(ctx.message.attachments)} fichier(s) terminé",
                color=discord.Color.green() if total_stats['added'] else discord.Color.orange()
            )

            # Résumé global
            embed.add_field(
                name="✅ Total FIDs bannis",
                value=f"{len(total_stats['added'])} FIDs ajoutés à la banlist",
                inline=False
            )

            if total_stats['already_banned']:
                embed.add_field(
                    name="ℹ️ Total déjà bannis",
                    value=f"{len(total_stats['already_banned'])} FIDs déjà dans la banlist",
                    inline=False
                )

            if total_stats['whitelisted']:
                embed.add_field(
                    name="⚠️ Total FIDs whitelistés (ignorés)",
                    value=f"{len(total_stats['whitelisted'])} FIDs sont whitelistés et n'ont pas été bannis",
                    inline=False
                )

            if total_stats['invalid']:
                invalid_sample = total_stats['invalid'][:5]
                embed.add_field(
                    name="❌ Total FIDs invalides",
                    value=f"{len(total_stats['invalid'])} FIDs invalides trouvés\nExemples: {', '.join(invalid_sample)}{'...' if len(total_stats['invalid']) > 5 else ''}",
                    inline=False
                )

            # Détails par fichier
            for filename, stats in file_stats.items():
                details = []
                if stats['added']:
                    details.append(f"✅ Bannis: {len(stats['added'])}")
                if stats['already_banned']:
                    details.append(f"ℹ️ Déjà bannis: {len(stats['already_banned'])}")
                if stats['whitelisted']:
                    details.append(f"⚠️ Whitelistés: {len(stats['whitelisted'])}")
                if stats['invalid']:
                    details.append(f"❌ Invalides: {len(stats['invalid'])}")
                
                embed.add_field(
                    name=f"📄 {filename}",
                    value="\n".join(details) or "Aucun FID traité",
                    inline=True
                )

            embed.set_footer(text="Utilisez !listbanned pour voir la liste complète")
            
            await status_msg.delete()
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error importing banlist: {e}")
            await status_msg.edit(content="❌ Une erreur est survenue lors de l'importation des fichiers.")

    @commands.command()
    async def premiumonly(self, ctx):
        """Active le mode premium uniquement pour les alertes Clanker"""
        self.premium_only = True
        await ctx.send("🥇 Mode premium activé - Seules les alertes des tokens premium seront affichées")

    @commands.command()
    async def premiumonlyoff(self, ctx):
        """Désactive le mode premium uniquement pour les alertes Clanker"""
        self.premium_only = False
        await ctx.send("✅ Mode premium désactivé - Toutes les alertes seront affichées")

    @commands.command()
    async def bankron(self, ctx):
        """Active les alertes pour les tokens déployés via Bankr"""
        self.bankr_enabled = True
        await ctx.send("✅ Alertes Bankr activées")

    @commands.command()
    async def bankroff(self, ctx):
        """Désactive les alertes pour les tokens déployés via Bankr"""
        self.bankr_enabled = False
        await ctx.send("❌ Alertes Bankr désactivées")

    @commands.command()
    async def imgon(self, ctx):
        """Active le filtre pour n'afficher que les tokens avec une image"""
        self.img_required = True
        await ctx.send("🖼️ Filtre image activé - Seuls les tokens avec une image seront affichés")

    @commands.command()
    async def imgoff(self, ctx):
        """Désactive le filtre d'image"""
        self.img_required = False
        await ctx.send("✅ Filtre image désactivé - Tous les tokens seront affichés")

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restart(self, ctx):
        """Redémarre le bot de manière sécurisée."""
        try:
            # Envoyer un message de confirmation
            await ctx.send("🔄 Redémarrage du bot en cours...")
            
            # Arrêter toutes les tâches en cours
            for cog in self.cogs.values():
                for task in cog.__dict__.values():
                    if isinstance(task, tasks.Loop):
                        task.cancel()
            
            # Attendre un court instant pour s'assurer que les tâches sont bien arrêtées
            await asyncio.sleep(1)
            
            # Redémarrer le bot
            await self.close()
            
            # Redémarrer le processus Python
            python = sys.executable
            os.execl(python, python, *sys.argv)
            
        except Exception as e:
            logger.error(f"Error during bot restart: {e}")
            await ctx.send("❌ Une erreur est survenue lors du redémarrage du bot.")

    async def setup_hook(self):
        """Initialize the bot's cogs and start monitoring tasks."""
        # Add cogs
        token_monitor = TokenMonitor(self)
        clanker_monitor = ClankerMonitor(self)
        
        await self.add_cog(token_monitor)
        await self.add_cog(clanker_monitor)
        
        # Cache initial tokens before starting monitoring
        try:
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0'
            }
            
            logger.info("Caching initial tokens...")
            response = requests.get(DEXSCREENER_API_URL, headers=headers)
            response.raise_for_status()
            tokens = response.json()
            
            # Add all current tokens to seen_tokens
            for token in tokens:
                chain_id = token.get('chainId', '').lower()
                token_address = token.get('tokenAddress')
                if chain_id in MONITORED_CHAINS and token_address:
                    token_key = f"{chain_id}:{token_address}"
                    token_monitor.seen_tokens.add(token_key)
            
            logger.info(f"Cached {len(token_monitor.seen_tokens)} initial tokens")
            
            # Cache initial Clanker tokens
            logger.info("Caching initial Clanker tokens...")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{CLANKER_API_URL}/tokens", params={"page": 1, "sort": "desc"})
                response.raise_for_status()
                data = response.json()
                if "data" in data:
                    for token in data["data"]:
                        token_address = token.get('contract_address')
                    if token_address:
                        clanker_monitor.seen_tokens.add(token_address)
                
                logger.info(f"Cached {len(clanker_monitor.seen_tokens)} initial Clanker tokens")
                
        except Exception as e:
            logger.error(f"Error caching initial tokens: {e}")
        
        # Start monitoring tasks
        token_monitor.monitor_tokens.start()
        token_monitor.check_trump_posts.start()
        clanker_monitor.monitor_clanker.start()
        clanker_monitor.monitor_clanker_volumes.start()

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        logger.info(f'Monitoring chains: {", ".join(MONITORED_CHAINS.values())}')

def main():
    """Main entry point for the bot."""
    try:
        if not DISCORD_TOKEN or not CHANNEL_ID:
            raise ValueError("Missing required environment variables")

        bot = Bot()
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 