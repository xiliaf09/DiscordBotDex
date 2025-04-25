import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Set

import discord
from discord.ext import tasks, commands
import requests
from dotenv import load_dotenv

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
DEXSCREENER_API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
BASE_CHAIN_ID = 8453
POLL_INTERVAL = 60  # seconds
SEEN_TOKENS_FILE = "seen_tokens.json"

class TokenMonitorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.seen_tokens: Set[str] = self._load_seen_tokens()
        self.channel = None
        
        # Add test command
        @self.command(name='test')
        async def test(ctx):
            """Send a test notification"""
            if ctx.channel.id == CHANNEL_ID:
                embed = discord.Embed(
                    title="Test Notification",
                    description="Ceci est un message test du bot DexBaseBot!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(
                    name="Status",
                    value="✅ Le bot fonctionne correctement!",
                    inline=False
                )
                await ctx.send(embed=embed)
                logger.info("Test notification sent successfully")

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

    async def setup_hook(self):
        """Setup tasks when bot is ready."""
        self.channel = self.get_channel(CHANNEL_ID)
        if not self.channel:
            logger.error(f"Could not find channel with ID {CHANNEL_ID}")
            return
        self.monitor_tokens.start()

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')

    @tasks.loop(seconds=POLL_INTERVAL)
    async def monitor_tokens(self):
        """Monitor for new tokens on Base blockchain."""
        try:
            response = requests.get(DEXSCREENER_API_URL)
            response.raise_for_status()
            tokens = response.json()

            # Filter for Base blockchain tokens
            base_tokens = [
                token for token in tokens
                if token.get('chainId') == BASE_CHAIN_ID
            ]

            # Find new tokens
            new_tokens = [
                token for token in base_tokens
                if token['address'] not in self.seen_tokens
            ]

            # Process new tokens
            for token in new_tokens:
                await self._send_token_notification(token)
                self.seen_tokens.add(token['address'])

            # Save updated seen tokens
            self._save_seen_tokens()

            if new_tokens:
                logger.info(f"Found {len(new_tokens)} new tokens")
            else:
                logger.debug("No new tokens found")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tokens: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    async def _send_token_notification(self, token: Dict):
        """Send a Discord notification for a new token."""
        try:
            embed = discord.Embed(
                title=f"New Token Detected: {token['name']}",
                description=f"Symbol: {token['symbol']}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="Contract Address",
                value=f"`{token['address']}`",
                inline=False
            )

            embed.add_field(
                name="Dexscreener Link",
                value=f"[View on Dexscreener](https://dexscreener.com/base/{token['address']})",
                inline=False
            )

            await self.channel.send(embed=embed)
            logger.info(f"Sent notification for token {token['name']}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    @monitor_tokens.before_loop
    async def before_monitor_tokens(self):
        """Wait until the bot is ready before starting the monitor."""
        await self.wait_until_ready()

def main():
    """Main entry point for the bot."""
    try:
        if not DISCORD_TOKEN or not CHANNEL_ID:
            raise ValueError("Missing required environment variables")

        bot = TokenMonitorBot()
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 