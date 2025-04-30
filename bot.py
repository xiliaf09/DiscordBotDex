import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Set
import time

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
MONITORED_CHAINS = {
    "base": "Base",
    "solana": "Solana"
}
POLL_INTERVAL = 2  # seconds
SEEN_TOKENS_FILE = "seen_tokens.json"
SEEN_CLANKER_TOKENS_FILE = "seen_clanker_tokens.json"
TRACKED_WALLETS_FILE = "tracked_wallets.json"
BANNED_FIDS_FILE = "banned_fids.json"

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

            await channel.send(embed=embed)
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
        embed.add_field(name="!fidcheck <contract>", value="Vérifie le FID associé à un contrat Clanker.", inline=False)
        await ctx.send(embed=embed)

class ClankerMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen_tokens: Set[str] = self._load_seen_tokens()
        self.channel = None
        self.is_active = True
        self.tracked_clanker_tokens = {}  # contract_address: {'first_seen': timestamp, 'alerted': False}
        self.default_volume_threshold = 5000
        self.banned_fids: Set[str] = self._load_banned_fids()

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
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Error loading banned FIDs: {e}")
            return set()

    def _save_banned_fids(self):
        """Save banned FIDs to file."""
        try:
            with open(BANNED_FIDS_FILE, 'w') as f:
                json.dump(list(self.banned_fids), f)
        except Exception as e:
            logger.error(f"Error saving banned FIDs: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def banfid(self, ctx, fid: str):
        """Bannir un FID pour ne plus recevoir ses alertes de déploiement."""
        if not fid.isdigit():
            await ctx.send("❌ Le FID doit être un nombre.")
            return
            
        self.banned_fids.add(fid)
        self._save_banned_fids()
        await ctx.send(f"✅ FID {fid} banni avec succès. Vous ne recevrez plus d'alertes de ce compte.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unbanfid(self, ctx, fid: str):
        """Débannir un FID pour recevoir à nouveau ses alertes de déploiement."""
        if fid in self.banned_fids:
            self.banned_fids.remove(fid)
            self._save_banned_fids()
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
                fid = social_context.get('fid')
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
            logger.info(f"[DEBUG] FID: {social_context.get('fid')}")

            # Vérifier si le FID est banni
            fid = str(social_context.get('fid', ''))
            if fid and fid in self.banned_fids:
                logger.info(f"Skipping notification for banned FID: {fid}")
                return

            # Filtrage selon la méthode de déploiement
            platform = social_context.get('platform', 'Unknown')
            interface = social_context.get('interface', 'Unknown')
            username = social_context.get('username')

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
                title="🆕 Nouveau Token Clanker",
                description=token_data.get('metadata', {}).get('description', 'Un nouveau token a été déployé sur Clanker!'),
                color=discord.Color(0x800080),
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

            # Add FID if available
            if fid:
                embed.add_field(
                    name="FID",
                    value=fid,
                    inline=True
                )

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

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)

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