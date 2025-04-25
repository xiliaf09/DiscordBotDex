import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Set

import discord
from discord.ext import tasks, commands
import requests
from dotenv import load_dotenv
import httpx
import feedparser

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

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/base"  # URL pour Base
TRUTH_SOCIAL_RSS_URL = "https://truthsocial.com/users/realDonaldTrump/feed.rss"
CLANKER_API_URL = "https://www.clanker.world/api"
MONITORED_CHAINS = {
    "base": "Base"
}
POLL_INTERVAL = 2  # seconds
SEEN_TOKENS_FILE = "seen_tokens.json"
SEEN_CLANKER_TOKENS_FILE = "seen_clanker_tokens.json"
MONITOR_STATES_FILE = "monitor_states.json"

class TokenMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen_tokens: Set[str] = self._load_seen_tokens()
        self.channel = None
        self.active_chains = self._load_monitor_states()
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

    def _load_monitor_states(self) -> dict:
        """Load saved monitor states from file."""
        try:
            if os.path.exists(MONITOR_STATES_FILE):
                with open(MONITOR_STATES_FILE, 'r') as f:
                    states = json.load(f)
                    return states.get('chains', {
                        "base": True
                    })
            return {
                "base": True
            }
        except Exception as e:
            logger.error(f"Error loading monitor states: {e}")
            return {
                "base": True
            }

    def _save_monitor_states(self):
        """Save current monitor states to file."""
        try:
            current_states = {
                'chains': self.active_chains,
                'clanker': self.bot.get_cog('ClankerMonitor').is_active if self.bot.get_cog('ClankerMonitor') else True
            }
            with open(MONITOR_STATES_FILE, 'w') as f:
                json.dump(current_states, f)
        except Exception as e:
            logger.error(f"Error saving monitor states: {e}")

    @commands.command()
    async def baseon(self, ctx):
        """Activer le monitoring pour Base"""
        self.active_chains["base"] = True
        self._save_monitor_states()
        await ctx.send("✅ Monitoring activé pour Base")

    @commands.command()
    async def baseoff(self, ctx):
        """Désactiver le monitoring pour Base"""
        self.active_chains["base"] = False
        self._save_monitor_states()
        await ctx.send("❌ Monitoring désactivé pour Base")

    @commands.command()
    async def status(self, ctx):
        """Afficher le statut du monitoring"""
        status_message = "📊 Statut du monitoring:\n"
        base_status = "✅ Activé" if self.active_chains.get("base", False) else "❌ Désactivé"
        status_message += f"Base: {base_status}\n"
        
        # Ajouter le statut de Clanker
        clanker_monitor = self.bot.get_cog('ClankerMonitor')
        if clanker_monitor:
            clanker_status = "✅ Activé" if clanker_monitor.is_active else "❌ Désactivé"
            status_message += f"Clanker: {clanker_status}"
        
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
            data = response.json()
            
            logger.info(f"Raw API response: {json.dumps(data, indent=2)}")
            
            # La structure de l'API retourne les tokens dans pairs
            pairs = data.get('pairs', [])
            if not pairs:
                logger.warning("No pairs found in API response")
                await status_msg.edit(content="❌ Aucun token récent trouvé sur Base.")
                return

            logger.info(f"Found {len(pairs)} pairs")
            
            # Prendre la paire la plus récente
            latest_pair = pairs[0]
            
            # Delete the status message
            await status_msg.delete()
            # Send token notification
            await self._send_token_notification(latest_pair, ctx.channel, "📊 Dernier Token sur")

        except Exception as e:
            logger.error(f"Error fetching latest token: {e}", exc_info=True)
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

    async def _send_token_notification(self, pair: Dict, channel: discord.TextChannel, title_prefix="🆕 Nouveau Token Détecté"):
        """Send a Discord notification for a token."""
        try:
            chain_name = "Base"
            
            # Set color for Base
            color = discord.Color.blue()
            
            # Get token data
            token_data = pair.get('baseToken', {})
            
            embed = discord.Embed(
                title=f"{title_prefix} {chain_name}",
                color=color,
                timestamp=datetime.now(timezone.utc)
            )

            # Add token information
            name = token_data.get('name', 'Unknown')
            symbol = token_data.get('symbol', 'Unknown')
            embed.add_field(name="Nom", value=name, inline=True)
            embed.add_field(name="Symbole", value=symbol, inline=True)

            # Add token address
            token_address = token_data.get('address')
            if token_address:
                embed.add_field(
                    name="📝 Adresse du Token",
                    value=f"`{token_address}`",
                    inline=False
                )

            # Add chain indicator emoji
            embed.add_field(
                name="Blockchain",
                value=f"⚡ {chain_name}",
                inline=True
            )

            # Add price information if available
            price_usd = pair.get('priceUsd')
            if price_usd:
                embed.add_field(
                    name="💰 Prix",
                    value=f"${float(price_usd):.8f}",
                    inline=True
                )

            # Add liquidity information if available
            liquidity_usd = pair.get('liquidity', {}).get('usd')
            if liquidity_usd:
                embed.add_field(
                    name="💧 Liquidité",
                    value=f"${float(liquidity_usd):,.2f}",
                    inline=True
                )

            # Add Dexscreener link
            pair_address = pair.get('pairAddress')
            if pair_address:
                dexscreener_url = f"https://dexscreener.com/base/{pair_address}"
                embed.add_field(
                    name="🔍 Dexscreener",
                    value=f"[Voir sur Dexscreener]({dexscreener_url})",
                    inline=False
                )

            await channel.send(embed=embed)
            logger.info(f"Sent notification for Base token: {name} ({symbol})")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            await channel.send("❌ Erreur lors de l'envoi de la notification du token.")

    @tasks.loop(seconds=POLL_INTERVAL)
    async def monitor_tokens(self):
        """Monitor for new tokens on Base."""
        try:
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0'
            }
            
            logger.info("Fetching latest token profiles...")
            response = requests.get(DEXSCREENER_API_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Get pairs from the response
            pairs = data.get('pairs', [])
            logger.info(f"Received {len(pairs)} pairs from API")

            # Filter for new tokens
            new_pairs = []
            for pair in pairs:
                token_data = pair.get('baseToken', {})
                token_address = token_data.get('address')
                
                if token_address:
                    token_key = f"base:{token_address}"
                    if token_key not in self.seen_tokens:
                        logger.info(f"New Base token found: {json.dumps(pair, indent=2)}")
                        new_pairs.append(pair)
                        self.seen_tokens.add(token_key)

            # Process new tokens
            for pair in new_pairs:
                await self._send_token_notification(pair, self.channel)

            # Save updated seen tokens
            if new_pairs:
                self._save_seen_tokens()
                logger.info(f"Found and processed {len(new_pairs)} new Base tokens")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tokens: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error in monitor_tokens: {e}", exc_info=True)

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
        """Wait until the bot is ready before starting the Trump posts check."""
        await self.bot.wait_until_ready()

class ClankerMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen_tokens: Set[str] = self._load_seen_tokens()
        self.channel = None
        self.is_active = self._load_monitor_state()
        self.last_check_time = datetime.now(timezone.utc)  # Initialisation avec timezone
        # La tâche sera démarrée dans setup_hook

    def cog_unload(self):
        """Called when the cog is unloaded."""
        self.monitor_clanker.cancel()

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

    def _load_monitor_state(self) -> bool:
        """Load saved Clanker monitor state from file."""
        try:
            if os.path.exists(MONITOR_STATES_FILE):
                with open(MONITOR_STATES_FILE, 'r') as f:
                    states = json.load(f)
                    return states.get('clanker', True)
            return True
        except Exception as e:
            logger.error(f"Error loading Clanker monitor state: {e}")
            return True

    def _save_monitor_state(self):
        """Save current Clanker monitor state to file."""
        try:
            current_states = {
                'chains': self.bot.get_cog('TokenMonitor').active_chains if self.bot.get_cog('TokenMonitor') else {"base": True},
                'clanker': self.is_active
            }
            with open(MONITOR_STATES_FILE, 'w') as f:
                json.dump(current_states, f)
        except Exception as e:
            logger.error(f"Error saving monitor states: {e}")

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string to datetime object with UTC timezone."""
        try:
            # Remplacer 'Z' par '+00:00' pour la compatibilité
            datetime_str = datetime_str.replace('Z', '+00:00')
            # Parser la date et s'assurer qu'elle a une timezone
            dt = datetime.fromisoformat(datetime_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception as e:
            logger.error(f"Error parsing datetime {datetime_str}: {e}")
            return datetime.now(timezone.utc)

    def _get_deployment_info(self, token_data: Dict) -> tuple:
        """Extract deployment method and link from token data."""
        # Log des données complètes du token pour le débogage
        logger.info(f"Raw token data for deployment info: {json.dumps(token_data, indent=2)}")
        
        social_context = token_data.get('social_context', '')
        cast_hash = token_data.get('cast_hash', '')
        tweet_id = token_data.get('tweet_id', '')
        
        logger.info(f"Processing deployment info - Social Context: {social_context}, Cast Hash: {cast_hash}, Tweet ID: {tweet_id}")
        
        deployment_method = "Interface Clanker"
        social_link = None

        # Vérifier Warpcast en priorité avec le cast_hash
        if cast_hash:
            deployment_method = "Warpcast"
            social_link = f"https://warpcast.com/{cast_hash}"
            logger.info(f"Detected Warpcast deployment with cast_hash: {cast_hash}")
        # Vérifier Twitter
        elif tweet_id:
            deployment_method = "Twitter"
            social_link = f"https://twitter.com/i/web/status/{tweet_id}"
            logger.info(f"Detected Twitter deployment with tweet_id: {tweet_id}")
        # Fallback sur le social_context
        elif social_context:
            if 'warpcast.com' in social_context or '/s0lverr/' in social_context:
                deployment_method = "Warpcast"
                if not social_context.startswith(('http://', 'https://')):
                    social_link = f"https://warpcast.com{social_context if social_context.startswith('/') else '/' + social_context}"
                else:
                    social_link = social_context
                logger.info(f"Detected Warpcast deployment from social_context: {social_context}")
            elif 'twitter.com' in social_context or 'x.com' in social_context:
                deployment_method = "Twitter"
                social_link = social_context
                logger.info(f"Detected Twitter deployment from social_context: {social_context}")

        logger.info(f"Final deployment info - Method: {deployment_method}, Link: {social_link}")
        return deployment_method, social_link

    @commands.command()
    async def clankeron(self, ctx):
        """Activer le monitoring pour Clanker"""
        self.is_active = True
        self._save_monitor_state()
        await ctx.send("✅ Monitoring Clanker activé")

    @commands.command()
    async def clankeroff(self, ctx):
        """Désactiver le monitoring pour Clanker"""
        self.is_active = False
        self._save_monitor_state()
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
                    if not tokens:
                        await status_msg.edit(content="❌ Aucun token trouvé sur Clanker.")
                        return

                    # Prendre le dernier token
                    latest_token = tokens[0]
                    
                    # Delete the status message
                    await status_msg.delete()
                    # Send token notification
                    await self._send_clanker_notification(latest_token, ctx.channel)

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
            deployment_method, social_link = self._get_deployment_info(token_data)
            
            embed = discord.Embed(
                title="🆕 Nouveau Token Clanker",
                description=token_data.get('metadata', {}).get('description', 'Un nouveau token a été déployé sur Clanker!'),
                color=discord.Color.blue(),
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

            embed.add_field(
                name="Contract",
                value=f"`{token_data.get('contract_address', 'Unknown')}`",
                inline=False
            )

            # Add pool information if available
            if token_data.get('pool_address'):
                embed.add_field(
                    name="Pool Address",
                    value=f"`{token_data['pool_address']}`",
                    inline=False
                )

            # Add deployment method and social link if available
            embed.add_field(
                name="Méthode de Déploiement",
                value=deployment_method,
                inline=True
            )

            if social_link:
                embed.add_field(
                    name="Lien Social",
                    value=social_link,
                    inline=False
                )

            # Add token image if available
            if token_data.get('img_url'):
                embed.set_thumbnail(url=token_data['img_url'])

            # Add market cap if available
            if market_cap := token_data.get('starting_market_cap'):
                embed.add_field(
                    name="Market Cap Initial",
                    value=f"${market_cap:,.2f}",
                    inline=True
                )

            await channel.send(embed=embed)
            logger.info(f"Clanker notification sent for token: {token_data.get('name')}")

        except Exception as e:
            logger.error(f"Error sending Clanker notification: {e}")
            await channel.send("❌ Erreur lors de l'envoi de la notification du token.")

    @tasks.loop(seconds=POLL_INTERVAL)
    async def monitor_clanker(self):
        """Monitor for new Clanker token deployments."""
        if not self.is_active:
            logger.debug("Clanker monitoring is disabled")
            return

        try:
            if not self.channel:
                self.channel = self.bot.get_channel(CHANNEL_ID)
                if not self.channel:
                    logger.error("Could not find channel for Clanker notifications")
                    return

            current_time = datetime.now(timezone.utc)
            logger.info(f"Checking for new Clanker tokens at {current_time}")

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
                    logger.info(f"Fetched {len(tokens)} tokens from Clanker API")

                    # Si c'est le premier démarrage
                    if self.last_check_time is None:
                        logger.info("First run - Initializing seen tokens")
                        # Ajouter tous les tokens actuels à seen_tokens
                        for token in tokens:
                            if contract_address := token.get('contract_address'):
                                self.seen_tokens.add(contract_address)
                                logger.debug(f"Added {token.get('name')} to seen tokens")
                        self._save_seen_tokens()
                        # Initialiser last_check_time avec la date actuelle
                        self.last_check_time = current_time
                        logger.info(f"Initialized last_check_time to {current_time}")
                        return

                    new_tokens_found = False
                    for token in tokens:
                        contract_address = token.get('contract_address')
                        if not contract_address:
                            logger.debug(f"Skipping token without contract address: {token.get('name')}")
                            continue

                        # Vérifier si c'est un nouveau token
                        created_at = self._parse_datetime(token.get('created_at'))
                        logger.info(f"Checking token {token.get('name')} - Created: {created_at}, Last check: {self.last_check_time}")
                        
                        # Si le token n'a pas déjà été vu et a été créé après le dernier check
                        if contract_address not in self.seen_tokens:
                            logger.info(f"Found new token: {token.get('name')} ({contract_address})")
                            new_tokens_found = True
                            await self._send_clanker_notification(token, self.channel)
                            self.seen_tokens.add(contract_address)

                    if new_tokens_found:
                        self._save_seen_tokens()
                        logger.info("Saved updated seen_tokens list")

                    # Mettre à jour le timestamp du dernier check
                    self.last_check_time = current_time
                    logger.info(f"Updated last_check_time to {current_time}")

                except httpx.ConnectError as e:
                    logger.error(f"Connection error to Clanker API: {e}")
                except httpx.TimeoutException as e:
                    logger.error(f"Timeout while connecting to Clanker API: {e}")
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error from Clanker API: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from Clanker API: {e}")

        except Exception as e:
            logger.error(f"Error monitoring Clanker: {e}", exc_info=True)

    @monitor_clanker.before_loop
    async def before_monitor_clanker(self):
        """Wait for bot to be ready before starting the Clanker monitoring loop."""
        await self.bot.wait_until_ready()
        logger.info("Starting Clanker monitoring loop")  # Added log to confirm loop start

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

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
                
                if isinstance(data, dict) and "data" in data:
                    tokens = data["data"]
                    for token in tokens:
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