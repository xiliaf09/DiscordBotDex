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
from eth_account import Account
import aiohttp
import sqlite3
from datetime import datetime
import config
from web3.middleware import geth_poa_middleware

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
ROUTER_ADDRESS = "0x327df1e6de05895d2ab08513aadd9313fe505d86"
CLANKER_FACTORY_ADDRESS = "0x2A787b2362021cC3eEa3C24C4748a6cD5B687382"
CLANKER_FACTORY_ABI = [
    {"inputs":[{"internalType":"address","name":"owner_","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
    {"inputs":[],"name":"Deprecated","type":"error"},
    {"inputs":[],"name":"InvalidCreatorInfo","type":"error"},
    {"inputs":[],"name":"InvalidCreatorReward","type":"error"},
    {"inputs":[],"name":"InvalidInterfaceInfo","type":"error"},
    {"inputs":[],"name":"InvalidTick","type":"error"},
    {"inputs":[],"name":"InvalidVaultConfiguration","type":"error"},
    {"inputs":[],"name":"NotFound","type":"error"},
    {"inputs":[],"name":"OnlyNonOriginatingChains","type":"error"},
    {"inputs":[],"name":"OnlyOriginatingChain","type":"error"},
    {"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},
    {"inputs":[],"name":"ReentrancyGuardReentrantCall","type":"error"},
    {"inputs":[],"name":"Unauthorized","type":"error"},
    {"inputs":[],"name":"ZeroTeamRewardRecipient","type":"error"},
    {"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"oldClankerDeployer","type":"address"},{"indexed":False,"internalType":"address","name":"newClankerDeployer","type":"address"}],"name":"ClankerDeployerUpdated","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"oldLocker","type":"address"},{"indexed":False,"internalType":"address","name":"newLocker","type":"address"}],"name":"LiquidityLockerUpdated","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"admin","type":"address"},{"indexed":False,"internalType":"bool","name":"isAdmin","type":"bool"}],"name":"SetAdmin","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":False,"internalType":"bool","name":"deprecated","type":"bool"}],"name":"SetDeprecated","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"tokenAddress","type":"address"},{"indexed":True,"internalType":"address","name":"creatorAdmin","type":"address"},{"indexed":True,"internalType":"address","name":"interfaceAdmin","type":"address"},{"indexed":False,"internalType":"address","name":"creatorRewardRecipient","type":"address"},{"indexed":False,"internalType":"address","name":"interfaceRewardRecipient","type":"address"},{"indexed":False,"internalType":"uint256","name":"positionId","type":"uint256"},{"indexed":False,"internalType":"string","name":"name","type":"string"},{"indexed":False,"internalType":"string","name":"symbol","type":"string"},{"indexed":False,"internalType":"int24","name":"startingTickIfToken0IsNewToken","type":"int24"},{"indexed":False,"internalType":"string","name":"metadata","type":"string"},{"indexed":False,"internalType":"uint256","name":"amountTokensBought","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"vaultDuration","type":"uint256"},{"indexed":False,"internalType":"uint8","name":"vaultPercentage","type":"uint8"},{"indexed":False,"internalType":"address","name":"msgSender","type":"address"}],"name":"TokenCreated","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"oldVault","type":"address"},{"indexed":False,"internalType":"address","name":"newVault","type":"address"}],"name":"VaultUpdated","type":"event"},
    {"inputs":[],"name":"MAX_CREATOR_REWARD","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MAX_TICK","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MAX_VAULT_PERCENTAGE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"POOL_FEE","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"TICK_SPACING","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"TOKEN_SUPPLY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"admins","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"claimRewards","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"components":[{"components":[{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"symbol","type":"string"},{"internalType":"bytes32","name":"salt","type":"bytes32"},{"internalType":"string","name":"image","type":"string"},{"internalType":"string","name":"metadata","type":"string"},{"internalType":"string","name":"context","type":"string"},{"internalType":"uint256","name":"originatingChainId","type":"uint256"}],"internalType":"struct IClanker.TokenConfig","name":"tokenConfig","type":"tuple"},{"components":[{"internalType":"uint8","name":"vaultPercentage","type":"uint8"},{"internalType":"uint256","name":"vaultDuration","type":"uint256"}],"internalType":"struct IClanker.VaultConfig","name":"vaultConfig","type":"tuple"},{"components":[{"internalType":"address","name":"pairedToken","type":"address"},{"internalType":"int24","name":"tickIfToken0IsNewToken","type":"int24"}],"internalType":"struct IClanker.PoolConfig","name":"poolConfig","type":"tuple"},{"components":[{"internalType":"uint24","name":"pairedTokenPoolFee","type":"uint24"},{"internalType":"uint256","name":"pairedTokenSwapAmountOutMinimum","type":"uint256"}],"internalType":"struct IClanker.InitialBuyConfig","name":"initialBuyConfig","type":"tuple"},{"components":[{"internalType":"uint256","name":"creatorReward","type":"uint256"},{"internalType":"address","name":"creatorAdmin","type":"address"},{"internalType":"address","name":"creatorRewardRecipient","type":"address"},{"internalType":"address","name":"interfaceAdmin","type":"address"},{"internalType":"address","name":"interfaceRewardRecipient","type":"address"}],"internalType":"struct IClanker.RewardsConfig","name":"rewardsConfig","type":"tuple"}],"internalType":"struct IClanker.DeploymentConfig","name":"deploymentConfig","type":"tuple"}],"name":"deployToken","outputs":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"positionId","type":"uint256"}],"stateMutability":"payable","type":"function"},
    {"inputs":[{"components":[{"components":[{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"symbol","type":"string"},{"internalType":"bytes32","name":"salt","type":"bytes32"},{"internalType":"string","name":"image","type":"string"},{"internalType":"string","name":"metadata","type":"string"},{"internalType":"string","name":"context","type":"string"},{"internalType":"uint256","name":"originatingChainId","type":"uint256"}],"internalType":"struct IClanker.TokenConfig","name":"tokenConfig","type":"tuple"},{"components":[{"internalType":"uint8","name":"vaultPercentage","type":"uint8"},{"internalType":"uint256","name":"vaultDuration","type":"uint256"}],"internalType":"struct IClanker.VaultConfig","name":"vaultConfig","type":"tuple"},{"components":[{"internalType":"address","name":"pairedToken","type":"address"},{"internalType":"int24","name":"tickIfToken0IsNewToken","type":"int24"}],"internalType":"struct IClanker.PoolConfig","name":"poolConfig","type":"tuple"},{"components":[{"internalType":"uint24","name":"pairedTokenPoolFee","type":"uint24"},{"internalType":"uint256","name":"pairedTokenSwapAmountOutMinimum","type":"uint256"}],"internalType":"struct IClanker.InitialBuyConfig","name":"initialBuyConfig","type":"tuple"},{"components":[{"internalType":"uint256","name":"creatorReward","type":"uint256"},{"internalType":"address","name":"creatorAdmin","type":"address"},{"internalType":"address","name":"creatorRewardRecipient","type":"address"},{"internalType":"address","name":"interfaceAdmin","type":"address"},{"internalType":"address","name":"interfaceRewardRecipient","type":"address"}],"internalType":"struct IClanker.RewardsConfig","name":"rewardsConfig","type":"tuple"}],"internalType":"struct IClanker.DeploymentConfig","name":"deploymentConfig","type":"tuple"},{"internalType":"address","name":"teamRewardRecipient","type":"address"}],"name":"deployTokenWithCustomTeamRewardRecipient","outputs":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"positionId","type":"uint256"}],"stateMutability":"payable","type":"function"},
    {"inputs":[{"components":[{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"symbol","type":"string"},{"internalType":"bytes32","name":"salt","type":"bytes32"},{"internalType":"string","name":"image","type":"string"},{"internalType":"string","name":"metadata","type":"string"},{"internalType":"string","name":"context","type":"string"},{"internalType":"uint256","name":"originatingChainId","type":"uint256"}],"internalType":"struct IClanker.TokenConfig","name":"tokenConfig","type":"tuple"},{"internalType":"address","name":"tokenAdmin","type":"address"}],"name":"deployTokenZeroSupply","outputs":[{"internalType":"address","name":"tokenAddress","type":"address"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"deploymentInfoForToken","outputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"positionId","type":"uint256"},{"internalType":"address","name":"locker","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"deprecated","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getTokensDeployedByUser","outputs":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"positionId","type":"uint256"},{"internalType":"address","name":"locker","type":"address"}],"internalType":"struct IClanker.DeploymentInfo[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"uniswapV3Factory_","type":"address"},{"internalType":"address","name":"positionManager_","type":"address"},{"internalType":"address","name":"swapRouter_","type":"address"},{"internalType":"address","name":"weth_","type":"address"},{"internalType":"address","name":"liquidityLocker_","type":"address"},{"internalType":"address","name":"vault_","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"liquidityLocker","outputs":[{"internalType":"contract ILpLockerv2","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"positionManager","outputs":[{"internalType":"contract INonfungiblePositionManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"admin","type":"address"},{"internalType":"bool","name":"isAdmin","type":"bool"}],"name":"setAdmin","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"bool","name":"deprecated_","type":"bool"}],"name":"setDeprecated","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"swapRouter","outputs":[{"internalType":"contract ISwapRouter","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"tokensDeployedByUsers","outputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"positionId","type":"uint256"},{"internalType":"address","name":"locker","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"uniswapV3Factory","outputs":[{"internalType":"contract IUniswapV3Factory","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"newLocker","type":"address"}],"name":"updateLiquidityLocker","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"newVault","type":"address"}],"name":"updateVault","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"vault","outputs":[{"internalType":"contract IClankerVault","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"weth","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]
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
TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
account = Account.from_key(config.WALLET_PRIVATE_KEY)

# Initialize database
def init_db():
    conn = sqlite3.connect('snipes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS active_snipes
                 (fid text, amount real, timestamp text)''')
    conn.commit()
    conn.close()

# Remplace l'ABI du router Uniswap V3
UNISWAP_V3_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Réinitialise le router avec la bonne ABI
router = w3.eth.contract(address=config.UNISWAP_V3_ROUTER, abi=UNISWAP_V3_ROUTER_ABI)

# Ajoute l'ABI minimale pour WETH (approve)
WETH_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [
            {"name": "", "type": "bool"}
        ],
        "type": "function"
    }
]

weth = w3.eth.contract(address=config.WETH_ADDRESS, abi=WETH_ABI)

# Ajout de la variable d'environnement pour QuickNode WebSocket
QUICKNODE_WSS = os.getenv('QUICKNODE_WSS')

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
            if token.get('contract_address'):
                photon_url = f"https://photon-base.tinyastro.io/en/lp/{token['contract_address']}"
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
        self.img_required = False
        self.tracked_clanker_tokens = {}
        self.default_volume_threshold = 5000
        logger.info("Loading banned and whitelisted FIDs...")
        self.banned_fids: Set[str] = self._load_banned_fids()
        self.whitelisted_fids: Set[str] = self._load_whitelisted_fids()
        logger.info(f"Loaded {len(self.banned_fids)} banned FIDs and {len(self.whitelisted_fids)} whitelisted FIDs")
        # --- Ajout Web3 WebSocket et contrat factory ---
        self.w3_ws = Web3(Web3.WebsocketProvider(QUICKNODE_WSS))
        self.w3_ws.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.clanker_factory = self.w3_ws.eth.contract(
            address=Web3.to_checksum_address(CLANKER_FACTORY_ADDRESS),
            abi=CLANKER_FACTORY_ABI
        )
        # ---

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

            # Add FID if available
            if fid:
                embed.add_field(
                    name="FID",
                    value=fid + (" 🥇" if is_premium else ""),
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

            # Créer la vue avec les boutons
            view = discord.ui.View()

            # Ajouter le bouton Ban si FID disponible
            if fid:
                ban_button = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="Ban",
                    custom_id=f"blacklist_{fid}"
                )
                view.add_item(ban_button)

                # Ajouter le bouton Remove Whitelist si token premium
                if is_premium:
                    remove_whitelist_button = discord.ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label="Remove Whitelist",
                        custom_id=f"removewhitelist_{fid}"
                    )
                    view.add_item(remove_whitelist_button)

            # Ajouter le bouton Photon si pool address disponible
            if token_data.get('pool_address'):
                photon_url = f"https://photon-base.tinyastro.io/en/lp/{token_data['pool_address']}"
                photon_button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Voir sur Photon",
                    url=photon_url
                )
                view.add_item(photon_button)

            # Envoyer le message avec les boutons
            await channel.send(embed=embed, view=view)

            logger.info(f"Clanker notification sent for token: {token_data.get('name')}")

            if contract_address:
                # Ajoute le token à la liste de surveillance du volume
                self.tracked_clanker_tokens[contract_address.lower()] = {
                    'first_seen': time.time(),
                    'alerted': False
                }
                logger.info(f"[VOLUME TRACK] Ajout du token {contract_address.lower()} à la surveillance volume")

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

    @tasks.loop(seconds=5)
    async def monitor_clanker_volumes(self):
        logger.info("[VOLUME CHECK] Tick de surveillance volume Clanker")
        if not self.is_active or not self.channel:
            return
        to_remove = []
        now = time.time()
        for contract_address, info in list(self.tracked_clanker_tokens.items()):
            age = now - info['first_seen']
            if age > 3600:
                to_remove.append(contract_address)
                continue
            if info.get('alerted'):
                continue
            # Appel Dexscreener
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url)
                    data = resp.json()
                    pairs = data.get('pairs', [])
                    if not pairs:
                        continue
                    pair = pairs[0]
                    volume_5m = float(pair.get('volume', {}).get('m5', 0))
                    symbol = pair.get('baseToken', {}).get('symbol', contract_address)
                    name = pair.get('baseToken', {}).get('name', contract_address)
                    threshold = self.default_volume_threshold
                    logger.info(f"[VOLUME CHECK] {name} ({symbol}) {contract_address} - Volume 5m: {volume_5m} USD (seuil: {threshold})")
                    if volume_5m >= threshold:
                        embed = discord.Embed(
                            title="🚨 Volume Clanker élevé!",
                            description=f"Le token {name} ({symbol}) a dépassé {threshold}$ de volume sur 5 minutes!",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.add_field(name="Contract", value=f"`{contract_address}`", inline=False)
                        embed.add_field(name="Volume (5m)", value=f"${volume_5m:,.2f}", inline=False)
                        embed.add_field(name="Dexscreener", value=f"[Voir]({pair.get('url', 'https://dexscreener.com')})", inline=False)
                        await self.channel.send(embed=embed)
                        self.tracked_clanker_tokens[contract_address]['alerted'] = True
                        logger.info(f"[VOLUME ALERT] Alerte volume envoyée pour {contract_address}")
            except Exception as e:
                logger.error(f"[VOLUME ERROR] Erreur lors de la vérification du volume Dexscreener pour {contract_address}: {e}")
        for contract_address in to_remove:
            del self.tracked_clanker_tokens[contract_address]
            logger.info(f"[VOLUME TRACK] Token {contract_address} retiré de la surveillance après une heure")

    @monitor_clanker_volumes.before_loop
    async def before_monitor_clanker_volumes(self):
        await self.bot.wait_until_ready()
        if not self.channel:
            self.channel = self.bot.get_channel(CHANNEL_ID)

    async def listen_onchain_clanker(self):
        await self.bot.wait_until_ready()
        if not self.channel:
            self.channel = self.bot.get_channel(CHANNEL_ID)
        channel = self.channel
        if not channel:
            logger.error("Could not find channel for Clanker notifications")
            return

        while True:  # Boucle principale de reconnexion
            try:
                # Création du filtre d'event TokenCreated
                event_filter = self.clanker_factory.events.TokenCreated.create_filter(fromBlock='latest')
                logger.info("Started on-chain Clanker event listener")

                # Récupération du SnipeMonitor pour accès aux snipes
                snipe_monitor = self.bot.get_cog('SnipeMonitor')

                while True:  # Boucle de lecture des événements
                    try:
                        for event in event_filter.get_new_entries():
                            token_address = event['args']['tokenAddress']
                            tx_hash = event['transactionHash']
                            tx = self.w3_ws.eth.get_transaction(tx_hash)
                            # Décodage des input data
                            try:
                                func_obj, func_args = self.clanker_factory.decode_function_input(tx['input'])
                                token_config = func_args['deploymentConfig']['tokenConfig']
                                name = token_config['name']
                                symbol = token_config['symbol']
                                image = token_config['image']
                                metadata = token_config['metadata']
                                context = token_config['context']
                                # Extraction du FID depuis le context (JSON)
                                fid = None
                                try:
                                    context_json = json.loads(context)
                                    fid = str(context_json.get('id'))
                                except Exception:
                                    pass
                                # --- Filtrage banlist/whitelist ---
                                if fid:
                                    if fid in self.banned_fids:
                                        logger.info(f"On-chain alert ignorée : FID {fid} banni.")
                                        continue
                                    if self.premium_only and fid not in self.whitelisted_fids:
                                        logger.info(f"On-chain alert ignorée : FID {fid} non whitelisté en mode premium_only.")
                                        continue
                                # ---
                                # Vérifier si le FID est whitelisté
                                is_premium = fid and fid in self.whitelisted_fids
                                # Envoie l'alerte Discord
                                embed = discord.Embed(
                                    title="🥇 Nouveau Token Clanker Premium (on-chain)" if is_premium else "🆕 Nouveau Token Clanker (on-chain)",
                                    color=discord.Color.gold() if is_premium else discord.Color.purple(),
                                    timestamp=datetime.now(timezone.utc)
                                )
                                embed.add_field(name="Nom du Token", value=name, inline=True)
                                embed.add_field(name="Ticker", value=symbol, inline=True)
                                embed.add_field(name="Adresse", value=f"`{token_address}`", inline=False)
                                # Ajout du lien Clanker.world
                                clanker_link = f"https://www.clanker.world/clanker/{token_address}"
                                embed.add_field(name="Lien Clanker", value=f"[Voir sur Clanker.world]({clanker_link})", inline=False)
                                if image:
                                    embed.set_thumbnail(url=image)
                                if fid:
                                    embed.add_field(name="FID", value=f"{fid} 🥇" if is_premium else fid, inline=True)
                                # Ajout des boutons Ban, Remove Whitelist et Photon
                                view = discord.ui.View()
                                if fid:
                                    ban_button = discord.ui.Button(
                                        style=discord.ButtonStyle.danger,
                                        label="Ban",
                                        custom_id=f"blacklist_{fid}"
                                    )
                                    view.add_item(ban_button)
                                if is_premium:
                                    remove_whitelist_button = discord.ui.Button(
                                        style=discord.ButtonStyle.danger,
                                        label="Remove Whitelist",
                                        custom_id=f"removewhitelist_{fid}"
                                    )
                                    view.add_item(remove_whitelist_button)
                                photon_button = discord.ui.Button(
                                    style=discord.ButtonStyle.primary,
                                    label="Voir sur Photon",
                                    url=f"https://photon-base.tinyastro.io/en/lp/{token_address}"
                                )
                                view.add_item(photon_button)
                                await channel.send(embed=embed, view=view)
                                logger.info(f"On-chain Clanker alert sent for {name} ({symbol}) {token_address}")
                                # Déclenchement du snipe instantané si FID match
                                if snipe_monitor and fid and fid in snipe_monitor.snipe_targets:
                                    snipe = snipe_monitor.snipe_targets[fid]
                                    if snipe['status'] == 'pending':
                                        success = await snipe_monitor.send_buy_webhook(token_address, snipe['amount'], snipe['gas_fees'])
                                        snipe['status'] = 'executed'
                                        snipe_monitor.snipe_targets[fid] = snipe
                                        snipe_channel = self.bot.get_channel(snipe['channel_id'])
                                        if snipe_channel:
                                            snipe_embed = discord.Embed(
                                                title="🎯 Snipe Exécuté (on-chain instantané)",
                                                description=f"Token Clanker trouvé pour le FID: `{fid}`",
                                                color=discord.Color.blue()
                                            )
                                            snipe_embed.add_field(name="Adresse", value=token_address, inline=True)
                                            snipe_embed.add_field(name="Montant", value=f"{snipe['amount']} ETH", inline=True)
                                            snipe_embed.add_field(name="Gas Fees", value=f"{snipe['gas_fees']} ETH", inline=True)
                                            snipe_embed.add_field(name="Status", value="✅ Webhook envoyé" if success else "❌ Webhook erreur", inline=True)
                                            await snipe_channel.send(embed=snipe_embed)
                                        logger.info(f"Snipe instantané exécuté pour FID {fid} sur {token_address} (webhook: {success})")
                            except Exception as e:
                                logger.error(f"Error decoding input data: {e}")
                        await asyncio.sleep(2)
                    except Exception as e:
                        if "filter not found" in str(e):
                            logger.warning("Filter expired, recreating...")
                            break  # Sort de la boucle interne pour recréer le filtre
                        else:
                            logger.error(f"Error in on-chain Clanker event loop: {e}")
                            await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error creating event filter: {e}")
                await asyncio.sleep(5)  # Attendre avant de réessayer de créer le filtre

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

    async def ensure_weth(self, amount_wei):
        """Wrap de l'ETH en WETH si le solde WETH est insuffisant."""
        weth_balance = w3.eth.get_balance(config.WETH_ADDRESS)
        if weth_balance < amount_wei:
            tx = weth.functions.deposit().build_transaction({
                'from': config.WALLET_ADDRESS,
                'value': amount_wei,
                'gas': 60000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(config.WALLET_ADDRESS),
            })
            signed_tx = w3.eth.account.sign_transaction(tx, config.WALLET_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"ETH wrapped to WETH, tx: {tx_hash.hex()}")
            return tx_hash.hex()
        return None

    async def ensure_approve(self, amount_wei):
        """Approve le routeur Uniswap V3 pour le WETH si besoin."""
        allowance = weth.functions.allowance(config.WALLET_ADDRESS, config.UNISWAP_V3_ROUTER).call()
        if allowance < amount_wei:
            tx = weth.functions.approve(config.UNISWAP_V3_ROUTER, 2**256-1).build_transaction({
                'from': config.WALLET_ADDRESS,
                'gas': 60000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(config.WALLET_ADDRESS),
            })
            signed_tx = w3.eth.account.sign_transaction(tx, config.WALLET_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Approve WETH for router, tx: {tx_hash.hex()}")
            return tx_hash.hex()
        return None

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buy(self, ctx, token_address: str, amount: float):
        """Achete un token via Uniswap V3 (exactInputSingle) en WETH (wrap auto si besoin)."""
        if amount <= 0:
            await ctx.send("❌ Le montant doit être supérieur à 0.")
            return
        try:
            amount_wei = w3.to_wei(amount, 'ether')
            # 1. Wrap ETH en WETH si besoin
            tx_hash_wrap = await self.ensure_weth(amount_wei)
            if tx_hash_wrap:
                await ctx.send(f"ETH wrap en WETH envoyé ! Hash: {tx_hash_wrap}. Attends la confirmation avant de swap.")
                # Optionnel : attendre la confirmation du wrap avant de continuer
            # 2. Approve le routeur si besoin
            tx_hash_approve = await self.ensure_approve(amount_wei)
            if tx_hash_approve:
                await ctx.send(f"Approve WETH envoyé ! Hash: {tx_hash_approve}. Attends la confirmation avant de swap.")
                # Optionnel : attendre la confirmation de l'approve
            # 3. Swap WETH -> token
            deadline = int(time.time()) + 300
            params = {
                'tokenIn': config.WETH_ADDRESS,
                'tokenOut': token_address,
                'fee': 3000,  # 0.3% pool
                'recipient': config.WALLET_ADDRESS,
                'deadline': deadline,
                'amountIn': amount_wei,
                'amountOutMinimum': 0,  # à ajuster pour le slippage
                'sqrtPriceLimitX96': 0
            }
            tx = router.functions.exactInputSingle(params).build_transaction({
                'from': config.WALLET_ADDRESS,
                'gas': config.GAS_LIMIT,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(config.WALLET_ADDRESS),
            })
            signed_tx = w3.eth.account.sign_transaction(tx, config.WALLET_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            embed = discord.Embed(
                title="🔄 Transaction Envoyée",
                description=f"Hash: {tx_hash.hex()}\nMontant: {amount} WETH",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error during buy: {e}")
            await ctx.send(f"❌ Erreur lors de l'achat: {str(e)}")

    async def execute_snipe(self, token_address: str, amount: float):
        """Exécute un snipe pour un token via Uniswap V3 (exactInputSingle) en WETH (wrap auto si besoin)."""
        try:
            amount_wei = w3.to_wei(amount, 'ether')
            await self.ensure_weth(amount_wei)
            await self.ensure_approve(amount_wei)
            deadline = int(time.time()) + 300
            params = {
                'tokenIn': config.WETH_ADDRESS,
                'tokenOut': token_address,
                'fee': 3000,  # 0.3% pool
                'recipient': config.WALLET_ADDRESS,
                'deadline': deadline,
                'amountIn': amount_wei,
                'amountOutMinimum': 0,  # à ajuster pour le slippage
                'sqrtPriceLimitX96': 0
            }
            tx = router.functions.exactInputSingle(params).build_transaction({
                'from': config.WALLET_ADDRESS,
                'gas': config.GAS_LIMIT,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(config.WALLET_ADDRESS),
            })
            signed_tx = w3.eth.account.sign_transaction(tx, config.WALLET_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            if self.channel:
                embed = discord.Embed(
                    title="🎯 Snipe Exécuté",
                    description=f"Token: {token_address}\nMontant: {amount} WETH",
                    color=discord.Color.green()
                )
                embed.add_field(name="Hash", value=tx_hash.hex(), inline=False)
                await self.channel.send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Error executing snipe: {e}")
            if self.channel:
                embed = discord.Embed(
                    title="❌ Erreur de Snipe",
                    description=f"Token: {token_address}\nMontant: {amount} WETH",
                    color=discord.Color.red()
                )
                embed.add_field(name="Erreur", value=str(e), inline=False)
                await self.channel.send(embed=embed)
            return False

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def deployclanker(self, ctx, name: str, symbol: str, fid: str, image: str, devbuy_eth: float = 0):
        """
        Déploie un token Clanker on-chain.
        Usage : !deployclanker "Nom" "TICKER" "FID" "url_image" montant_eth
        """
        try:
            import binascii
            # Salt unique (32 bytes)
            salt_bytes = os.urandom(32)
            # Metadata JSON
            metadata = json.dumps({
                "description": f"Token {name} déployé via Discord",
                "socialMediaUrls": [],
                "auditUrls": []
            })
            # Context JSON
            context = json.dumps({
                "interface": "clanker.world",
                "platform": "farcaster",
                "messageId": "",
                "id": fid
            })
            # TokenConfig
            token_config = (
                name,
                symbol,
                salt_bytes,
                image,
                metadata,
                context,
                8453  # Base chainId
            )
            # VaultConfig (pas de vesting par défaut)
            vault_config = (
                0,  # percentage
                0   # duration
            )
            # PoolConfig
            pool_config = (
                Web3.to_checksum_address(config.WETH_ADDRESS),
                -230400  # tickIfToken0IsNewToken
            )
            # InitialBuyConfig
            initial_buy_config = (
                10000,  # pool fee (1%)
                0       # min out
            )
            # RewardsConfig
            creator_admin = Web3.to_checksum_address(config.WALLET_ADDRESS)
            interface_admin = Web3.to_checksum_address("0xEea96d959963EaB488A3d4B7d5d347785cf1Eab8")
            interface_reward = Web3.to_checksum_address("0x1eaf444ebDf6495C57aD52A04C61521bBf564ace")
            rewards_config = (
                8000,  # 80% creator reward
                creator_admin,
                creator_admin,
                interface_admin,
                interface_reward
            )
            deployment_config = (
                token_config,
                vault_config,
                pool_config,
                initial_buy_config,
                rewards_config
            )
            contract = self.clanker_factory
            value = self.w3_ws.to_wei(devbuy_eth, 'ether') if devbuy_eth > 0 else 0
            tx = contract.functions.deployToken(deployment_config)
            tx_dict = tx.build_transaction({
                'from': creator_admin,
                'value': value,
                'nonce': self.w3_ws.eth.get_transaction_count(creator_admin),
                'gas': 2_500_000,
                'gasPrice': self.w3_ws.eth.gas_price
            })
            signed = self.w3_ws.eth.account.sign_transaction(tx_dict, config.WALLET_PRIVATE_KEY)
            tx_hash = self.w3_ws.eth.send_raw_transaction(signed.rawTransaction)
            await ctx.send(f"✅ Transaction envoyée ! Hash : `{tx_hash.hex()}`. Attente du déploiement...")
            receipt = self.w3_ws.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            logs = contract.events.TokenCreated().process_receipt(receipt)
            if logs:
                token_addr = logs[0]['args']['tokenAddress']
                clanker_link = f"https://www.clanker.world/clanker/{token_addr}"
                await ctx.send(f"🎉 Token déployé ! Adresse : `{token_addr}`\nLien Clanker : {clanker_link}")
            else:
                await ctx.send("⚠️ Token déployé mais impossible de trouver l'adresse dans les logs.")
        except Exception as e:
            logger.error(f"[DEPLOY] Erreur lors du déploiement : {e}")
            await ctx.send(f"❌ Erreur lors du déploiement : {e}")

class SnipeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipe_targets = {}
        self.is_monitoring = False
        self.channel = None

    async def send_buy_webhook(self, token_address: str, amount_eth: float, gas_fees: float = None):
        url = "https://clankersniper-production.up.railway.app/buy_webhook"
        payload = {
            "token_address": token_address,
            "amount_eth": amount_eth
        }
        if gas_fees is not None:
            payload["gas_fees"] = gas_fees
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Erreur webhook: {resp.status} - {text}")
                    return False

    @commands.command(name="buywebhook")
    @commands.has_permissions(administrator=True)
    async def buywebhook(self, ctx, contract: str, amount: float, gas_fees: float):
        """Déclenche un achat via le webhook Telegram avec gas fees."""
        success = await self.send_buy_webhook(contract, amount, gas_fees)
        if success:
            await ctx.send(f"✅ Achat déclenché via le webhook pour {contract} ({amount} ETH, gas: {gas_fees} ETH)")
        else:
            await ctx.send("❌ Erreur lors de l'appel du webhook Telegram.")

    async def monitor_new_clankers(self):
        """Surveille les nouveaux Clankers via l'API et déclenche le sniping si correspondance FID"""
        seen_contracts = set()
        while self.is_monitoring:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://www.clanker.world/api/tokens", params={"page": 1, "sort": "desc"}) as resp:
                        if resp.status != 200:
                            logger.error(f"Erreur API Clanker: {resp.status}")
                            await asyncio.sleep(2)
                            continue
                        data = await resp.json()
                        tokens = data.get("data", [])
                        for token in tokens:
                            contract = token.get("contract_address")
                            fid = str(token.get("requestor_fid"))
                            if not contract or not fid:
                                continue
                            if contract in seen_contracts:
                                continue
                            if fid in self.snipe_targets and self.snipe_targets[fid]["status"] == "pending":
                                target = self.snipe_targets[fid]
                                success = await self.send_buy_webhook(contract, target['amount'], target['gas_fees'])
                                target['status'] = 'executed'
                                seen_contracts.add(contract)
                                channel = self.bot.get_channel(target['channel_id'])
                                if channel:
                                    embed = discord.Embed(
                                        title="🎯 Snipe Détecté!",
                                        description=f"Token Clanker trouvé pour le FID: `{fid}`",
                                        color=discord.Color.blue()
                                    )
                                    embed.add_field(name="Adresse", value=contract, inline=True)
                                    embed.add_field(name="Montant", value=f"{target['amount']} ETH", inline=True)
                                    embed.add_field(name="Gas Fees", value=f"{target['gas_fees']} ETH", inline=True)
                                    embed.add_field(name="Status", value="✅ Webhook envoyé" if success else "❌ Webhook erreur", inline=True)
                                    await channel.send(embed=embed)
                                logger.info(f"Snipe exécuté pour FID {fid} sur {contract} (webhook: {success})")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Erreur dans monitor_new_clankers: {e}")
                await asyncio.sleep(5)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def snipe(self, ctx, fid: str, amount: float, gas_fees: float):
        """Commande pour sniper un token Clanker spécifique basé sur son FID, montant et gas fees"""
        try:
            if amount <= 0:
                await ctx.send("❌ Le montant doit être supérieur à 0")
                return
            if gas_fees <= 0:
                await ctx.send("❌ Les gas fees doivent être supérieurs à 0")
                return
            self.snipe_targets[fid] = {
                'amount': amount,
                'gas_fees': gas_fees,
                'channel_id': ctx.channel.id,
                'user_id': ctx.author.id,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            embed = discord.Embed(
                title="🎯 Snipe Configuré",
                description=f"Le bot va maintenant surveiller les nouveaux Clankers avec le FID: `{fid}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Montant", value=f"{amount} ETH", inline=True)
            embed.add_field(name="Gas Fees", value=f"{gas_fees} ETH", inline=True)
            embed.add_field(name="Status", value="⏳ En attente", inline=True)
            await ctx.send(embed=embed)
            if not self.is_monitoring:
                self.is_monitoring = True
                asyncio.create_task(self.monitor_new_clankers())
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du snipe: {e}")
            await ctx.send(f"❌ Erreur: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def listsnipes(self, ctx):
        """Liste tous les snipes en attente"""
        if not self.snipe_targets:
            await ctx.send("📝 Aucun snipe en attente")
            return

        embed = discord.Embed(
            title="📝 Liste des Snipes",
            description="Voici tous les snipes en attente :",
            color=discord.Color.blue()
        )

        for fid, data in self.snipe_targets.items():
            if data['status'] == 'pending':
                embed.add_field(
                    name=f"FID: {fid}",
                    value=f"Montant: {data['amount']} ETH\nStatus: {data['status']}\nCréé le: {data['created_at']}",
                    inline=False
                )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def cancelsnipe(self, ctx, fid: str):
        """Annule un snipe en attente"""
        if fid not in self.snipe_targets:
            await ctx.send(f"❌ Aucun snipe trouvé pour le FID: {fid}")
            return

        if self.snipe_targets[fid]['status'] != 'pending':
            await ctx.send(f"❌ Ce snipe n'est plus en attente (status: {self.snipe_targets[fid]['status']})")
            return

        del self.snipe_targets[fid]
        await ctx.send(f"✅ Snipe annulé pour le FID: {fid}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def editsnipe(self, ctx, fid: str, new_amount: float):
        """Modifie le montant d'un snipe en attente"""
        if fid not in self.snipe_targets:
            await ctx.send(f"❌ Aucun snipe trouvé pour le FID: {fid}")
            return

        if self.snipe_targets[fid]['status'] != 'pending':
            await ctx.send(f"❌ Ce snipe n'est plus en attente (status: {self.snipe_targets[fid]['status']})")
            return

        if new_amount <= 0:
            await ctx.send("❌ Le nouveau montant doit être supérieur à 0")
            return

        old_amount = self.snipe_targets[fid]['amount']
        self.snipe_targets[fid]['amount'] = new_amount

        embed = discord.Embed(
            title="✏️ Snipe Modifié",
            description=f"Le montant du snipe pour le FID {fid} a été modifié",
            color=discord.Color.blue()
        )
        embed.add_field(name="Ancien montant", value=f"{old_amount} ETH", inline=True)
        embed.add_field(name="Nouveau montant", value=f"{new_amount} ETH", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearsnipes(self, ctx):
        """Supprime tous les snipes en attente"""
        if not self.snipe_targets:
            await ctx.send("📝 Aucun snipe à supprimer")
            return

        count = len(self.snipe_targets)
        self.snipe_targets.clear()
        await ctx.send(f"🗑️ {count} snipes ont été supprimés")

    async def send_telegram_command(self, command):
        """Envoie la commande au bot Telegram"""
        try:
            # Configuration de la requête
            payload = {
                "chat_id": TELEGRAM_USER_ID,
                "text": command,
                "parse_mode": "HTML"
            }
            
            # Envoi de la requête
            async with aiohttp.ClientSession() as session:
                async with session.post(TELEGRAM_API_URL, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Commande Telegram envoyée avec succès: {command}")
                        return True
                    else:
                        logger.error(f"Erreur lors de l'envoi de la commande Telegram: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la commande Telegram: {e}")
            return False

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def testtelegram(self, ctx):
        """Teste la connexion avec le bot Telegram en envoyant un message test."""
        try:
            # Message initial
            status_msg = await ctx.send("🔄 Test de la connexion Telegram en cours...")

            # Envoyer un message test au bot Telegram
            test_command = "/test"
            success = await self.send_telegram_command(test_command)

            if success:
                await status_msg.edit(content="✅ Connexion Telegram réussie! Le message test a été envoyé.")
            else:
                await status_msg.edit(content="❌ Erreur lors de l'envoi du message test à Telegram.")

        except Exception as e:
            logger.error(f"Erreur lors du test Telegram: {e}")
            await ctx.send(f"❌ Erreur lors du test: {str(e)}")

    @commands.command(name="buytg")
    @commands.has_permissions(administrator=True)
    async def buytg(self, ctx, contract: str, amount: float):
        """Envoie immédiatement la commande /buy <contract> <amount> au bot Telegram."""
        try:
            if amount <= 0:
                await ctx.send("❌ Le montant doit être supérieur à 0.")
                return
            telegram_command = f"/buy {contract} {amount}"
            success = await self.send_telegram_command(telegram_command)
            if success:
                await ctx.send(f"✅ Commande envoyée à Telegram : {telegram_command}")
            else:
                await ctx.send("❌ Erreur lors de l'envoi de la commande à Telegram.")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la commande buytg à Telegram: {e}")
            await ctx.send(f"❌ Erreur : {str(e)}")

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=config.COMMAND_PREFIX, intents=intents, help_command=None)

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
        snipe_monitor = SnipeMonitor(self)
        
        await self.add_cog(token_monitor)
        await self.add_cog(clanker_monitor)
        await self.add_cog(snipe_monitor)
        
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
        # clanker_monitor.monitor_clanker.start()  # Supprimé car remplacé par l'écoute on-chain
        clanker_monitor.monitor_clanker_volumes.start()
        # snipe_monitor.monitor_snipes.start()  # Cette ligne est supprimée car nous n'utilisons plus monitor_snipes
        # Lancer la tâche d'écoute on-chain
        asyncio.create_task(clanker_monitor.listen_onchain_clanker())

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