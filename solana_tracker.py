import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, List, Callable, Optional
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Commitment
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solders.signature import Signature
import config
from solana_database import SolanaDatabase

logger = logging.getLogger(__name__)

class SolanaTracker:
    def __init__(self, rpc_url: str = None, ws_url: str = None):
        self.rpc_url = rpc_url or config.SOLANA_RPC_URL
        self.ws_url = ws_url or config.SOLANA_WS_URL
        self.client = None
        self.ws_connection = None
        self.db = SolanaDatabase()
        self.tracked_addresses = set()
        self.notification_callbacks = []
        self.is_running = False
        
    async def initialize(self):
        """Initialize the Solana client and WebSocket connection"""
        try:
            self.client = AsyncClient(self.rpc_url)
            # Test connection with get_version instead of get_health
            version = await self.client.get_version()
            logger.info(f"Solana RPC client initialized successfully - Version: {version.value}")
            
            # Load tracked addresses from database
            await self.load_tracked_addresses()
            
        except Exception as e:
            logger.error(f"Error initializing Solana client: {e}")
            raise
    
    async def load_tracked_addresses(self):
        """Load tracked addresses from database"""
        try:
            addresses = self.db.get_tracked_addresses()
            self.tracked_addresses = {addr['address'] for addr in addresses}
            logger.info(f"Loaded {len(self.tracked_addresses)} tracked addresses")
        except Exception as e:
            logger.error(f"Error loading tracked addresses: {e}")
    
    def add_notification_callback(self, callback: Callable):
        """Add a notification callback function"""
        self.notification_callbacks.append(callback)
    
    async def start_tracking(self):
        """Start tracking addresses via WebSocket"""
        if not self.tracked_addresses:
            logger.warning("No addresses to track")
            return
        
        try:
            # Create WebSocket connection
            self.ws_connection = await connect(self.ws_url)
            
            # Subscribe to account changes for each tracked address
            for address in self.tracked_addresses:
                try:
                    pubkey = Pubkey.from_string(address)
                    await self.ws_connection.account_subscribe(
                        pubkey,
                        commitment=Commitment("confirmed"),
                        encoding="jsonParsed"
                    )
                    logger.info(f"Subscribed to account changes for {address}")
                except Exception as e:
                    logger.error(f"Error subscribing to {address}: {e}")
            
            self.is_running = True
            logger.info("Started tracking addresses")
            
            # Listen for messages
            async for message in self.ws_connection:
                if not self.is_running:
                    break
                    
                await self.handle_websocket_message(message)
                
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
        finally:
            if self.ws_connection:
                await self.ws_connection.close()
    
    async def handle_websocket_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            if hasattr(message, 'value') and message.value:
                # This is an account change notification
                account_data = message.value
                address = str(account_data.account)
                
                if address in self.tracked_addresses:
                    await self.process_account_change(address, account_data)
                    
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def process_account_change(self, address: str, account_data):
        """Process account change and get recent transactions"""
        try:
            # Get recent transactions for this address
            recent_txs = await self.get_recent_transactions(address)
            
            for tx in recent_txs:
                await self.process_transaction(address, tx)
                
        except Exception as e:
            logger.error(f"Error processing account change for {address}: {e}")
    
    async def get_recent_transactions(self, address: str, limit: int = 10) -> List[Dict]:
        """Get recent transactions for an address"""
        try:
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_signatures_for_address(
                pubkey, 
                limit=limit,
                commitment=Commitment("confirmed")
            )
            
            transactions = []
            for sig_info in response.value:
                # Get transaction details
                tx_response = await self.client.get_transaction(
                    Signature.from_string(sig_info.signature),
                    commitment=Commitment("confirmed"),
                    max_supported_transaction_version=0
                )
                
                if tx_response.value:
                    tx_data = tx_response.value
                    transactions.append({
                        'signature': sig_info.signature,
                        'slot': sig_info.slot,
                        'block_time': sig_info.block_time,
                        'transaction': tx_data
                    })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting recent transactions for {address}: {e}")
            return []
    
    async def process_transaction(self, address: str, tx_data: Dict):
        """Process a transaction and send notifications if needed"""
        try:
            signature = tx_data['signature']
            
            # Check if we already processed this transaction
            existing_txs = self.db.get_recent_transactions(address, limit=100)
            if any(tx['signature'] == signature for tx in existing_txs):
                return
            
            # Analyze transaction type and amount
            tx_info = await self.analyze_transaction(tx_data['transaction'])
            
            # Store in database
            self.db.add_transaction(
                address=address,
                signature=signature,
                transaction_type=tx_info['type'],
                amount=tx_info.get('amount'),
                token_mint=tx_info.get('token_mint'),
                block_time=tx_data.get('block_time'),
                slot=tx_data.get('slot')
            )
            
            # Check notification settings
            settings = self.db.get_notification_settings(address)
            if settings and self.should_notify(tx_info, settings):
                await self.send_notification(address, signature, tx_info)
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
    
    async def analyze_transaction(self, transaction) -> Dict:
        """Analyze transaction to determine type and extract relevant data"""
        try:
            # Basic transaction analysis
            tx_info = {
                'type': 'unknown',
                'amount': None,
                'token_mint': None
            }
            
            if hasattr(transaction, 'transaction') and transaction.transaction:
                tx = transaction.transaction
                
                # Check for token transfers
                if hasattr(tx, 'message') and tx.message:
                    message = tx.message
                    
                    # Look for token transfer instructions
                    if hasattr(message, 'instructions'):
                        for instruction in message.instructions:
                            if hasattr(instruction, 'program_id'):
                                program_id = str(instruction.program_id)
                                
                                # Token Program
                                if program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                                    tx_info['type'] = 'token_transfer'
                                    # Extract token mint and amount from instruction data
                                    # This is a simplified version - you'd need to parse the instruction data properly
                                
                                # System Program
                                elif program_id == "11111111111111111111111111111111":
                                    tx_info['type'] = 'sol_transfer'
                                
                                # DEX Program (like Raydium, Orca, etc.)
                                elif program_id in [
                                    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium
                                    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca
                                ]:
                                    tx_info['type'] = 'dex_swap'
            
            return tx_info
            
        except Exception as e:
            logger.error(f"Error analyzing transaction: {e}")
            return {'type': 'unknown', 'amount': None, 'token_mint': None}
    
    def should_notify(self, tx_info: Dict, settings: Dict) -> bool:
        """Check if we should send a notification based on settings"""
        try:
            # Check minimum amount
            if settings.get('min_amount', 0) > 0:
                if not tx_info.get('amount') or tx_info['amount'] < settings['min_amount']:
                    return False
            
            # Check notification types
            notification_types = settings.get('notification_types', 'all')
            if notification_types != 'all':
                allowed_types = notification_types.split(',')
                if tx_info['type'] not in allowed_types:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification settings: {e}")
            return True
    
    async def send_notification(self, address: str, signature: str, tx_info: Dict):
        """Send notification to all registered callbacks"""
        try:
            notification_data = {
                'address': address,
                'signature': signature,
                'transaction_type': tx_info['type'],
                'amount': tx_info.get('amount'),
                'token_mint': tx_info.get('token_mint'),
                'timestamp': datetime.now().isoformat()
            }
            
            for callback in self.notification_callbacks:
                try:
                    await callback(notification_data)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def add_address(self, address: str, nickname: str = None, added_by: str = "system"):
        """Add a new address to track"""
        try:
            # Validate address
            Pubkey.from_string(address)
            
            # Add to database
            success = self.db.add_tracked_address(address, nickname, added_by)
            if success:
                self.tracked_addresses.add(address)
                logger.info(f"Added address to tracking: {address}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding address {address}: {e}")
            return False
    
    async def remove_address(self, address: str):
        """Remove an address from tracking"""
        try:
            success = self.db.remove_tracked_address(address)
            if success:
                self.tracked_addresses.discard(address)
                logger.info(f"Removed address from tracking: {address}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing address {address}: {e}")
            return False
    
    async def stop_tracking(self):
        """Stop tracking and close connections"""
        try:
            self.is_running = False
            if self.ws_connection:
                await self.ws_connection.close()
            if self.client:
                await self.client.close()
            logger.info("Stopped tracking")
        except Exception as e:
            logger.error(f"Error stopping tracking: {e}")
    
    def get_tracked_addresses(self) -> List[Dict]:
        """Get list of tracked addresses"""
        return self.db.get_tracked_addresses()
    
    def get_recent_activity(self, address: str = None, limit: int = 20) -> List[Dict]:
        """Get recent activity for an address or all addresses"""
        return self.db.get_recent_transactions(address, limit)
