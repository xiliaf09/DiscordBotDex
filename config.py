import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))

# Base Network Configuration
BASE_RPC_URL = os.getenv('BASE_RPC_URL')
WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')

# Uniswap V3 Configuration
UNISWAP_V3_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"  # Base Uniswap V3 Router
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"  # WETH on Base

# Clanker Configuration
CLANKER_API_KEY = os.getenv('CLANKER_API_KEY')
CLANKER_API_SECRET = os.getenv('CLANKER_API_SECRET')

# Sniping Configuration
DEFAULT_SLIPPAGE = 100  # 1%
GAS_LIMIT = 300000
PRIORITY_FEE = 1.5  # gwei

# Command Prefix
COMMAND_PREFIX = "!"

# Database Configuration (for storing active snipes)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///snipes.db')

# Pushover Configuration (for critical volume alerts)
PUSHOVER_API_TOKEN = os.getenv('PUSHOVER_API_TOKEN')
PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY')

# Pushover Configuration for second user (optional)
PUSHOVER_API_TOKEN_2 = os.getenv('PUSHOVER_API_TOKEN_2')
PUSHOVER_USER_KEY_2 = os.getenv('PUSHOVER_USER_KEY_2')

# Twilio Configuration (for phone calls on critical volume alerts)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER') 