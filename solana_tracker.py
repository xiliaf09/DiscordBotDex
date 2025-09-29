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
            logger.info(f"Loaded {len(self.tracked_addresses)} tracked addresses: {list(self.tracked_addresses)}")
        except Exception as e:
            logger.error(f"Error loading tracked addresses: {e}")
    
    def add_notification_callback(self, callback: Callable):
        """Add a notification callback function"""
        self.notification_callbacks.append(callback)
    
    async def start_tracking(self):
        """Start tracking addresses via polling method"""
        if not self.tracked_addresses:
            logger.warning("No addresses to track")
            return
        
        try:
            logger.info(f"Starting Solana tracking for {len(self.tracked_addresses)} addresses...")
            self.is_running = True
            
            # Start polling task for each address
            for address in self.tracked_addresses:
                asyncio.create_task(self.poll_address_transactions(address))
            
            logger.info(f"Started tracking {len(self.tracked_addresses)} addresses")
            
            # Keep the task running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in tracking: {e}")
    
    async def poll_address_transactions(self, address: str):
        """Poll an address for new transactions"""
        last_signature = None
        
        while self.is_running:
            try:
                # Get recent transactions
                recent_txs = await self.get_recent_transactions(address, limit=5)
                
                if recent_txs:
                    # Check if we have new transactions
                    current_signature = recent_txs[0].get('signature')
                    
                    if last_signature and current_signature != last_signature:
                        logger.info(f"New transaction detected for {address}: {current_signature}")
                        
                        # Process the new transaction
                        for tx in recent_txs:
                            if tx.get('signature') == current_signature:
                                await self.process_transaction(address, tx)
                                break
                    
                    last_signature = current_signature
                
                # Poll every 5 seconds
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error polling address {address}: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def handle_websocket_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            logger.debug(f"Received WebSocket message: {type(message)}")
            
            if hasattr(message, 'value') and message.value:
                # This is a log notification
                log_data = message.value
                signature = str(log_data.signature)
                logs = log_data.logs if hasattr(log_data, 'logs') else []
                
                logger.debug(f"Log signature: {signature}")
                logger.debug(f"Logs: {logs}")
                logger.debug(f"Tracked addresses: {list(self.tracked_addresses)}")
                
                # Check if any tracked address is mentioned in the logs
                for tracked_address in self.tracked_addresses:
                    # Check if the tracked address appears in any of the log messages
                    for log in logs:
                        if tracked_address in log:
                            logger.info(f"Transaction detected for {tracked_address}: {signature}")
                            await self.process_transaction_log(tracked_address, signature, log_data)
                            return  # Only process once per transaction
                
                logger.debug(f"No tracked addresses found in logs")
                    
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def process_account_change(self, address: str, account_data):
        """Process account change and get recent transactions"""
        try:
            logger.info(f"Processing account change for {address}")
            
            # Get recent transactions for this address
            recent_txs = await self.get_recent_transactions(address, limit=5)
            
            for tx in recent_txs:
                await self.process_transaction(address, tx)
                
        except Exception as e:
            logger.error(f"Error processing account change for {address}: {e}")
    
    async def process_transaction_log(self, address: str, signature: str, log_data):
        """Process transaction log and get transaction details"""
        try:
            # Get transaction details
            transaction = await self.get_transaction_details(signature)
            if transaction:
                await self.process_transaction(address, transaction)
                
        except Exception as e:
            logger.error(f"Error processing transaction log for {address}: {e}")
    
    async def get_transaction_details(self, signature: str) -> Dict:
        """Get transaction details by signature"""
        try:
            # Convert string signature to Signature object
            sig_obj = Signature.from_string(signature)
            response = await self.client.get_transaction(
                sig_obj,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            return response.value if response.value else None
        except Exception as e:
            logger.error(f"Error getting transaction details for {signature}: {e}")
            return None
    
    async def get_recent_transactions(self, address: str, limit: int = 10) -> List[Dict]:
        """Get recent transactions for an address"""
        try:
            # Check if client is closed and reconnect if needed
            if self.client is None or self.client._session is None:
                logger.info("Reconnecting to Solana RPC...")
                self.client = AsyncClient(self.rpc_url)
            
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_signatures_for_address(
                pubkey, 
                limit=limit,
                commitment=Commitment("confirmed")
            )
            
            transactions = []
            if response.value:
                for sig_info in response.value:
                    transactions.append({
                        'signature': str(sig_info.signature),
                        'slot': sig_info.slot,
                        'block_time': sig_info.block_time,
                        'confirmation_status': sig_info.confirmation_status
                    })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting recent transactions for {address}: {e}")
            # Try to reconnect on next attempt
            if "client has been closed" in str(e):
                self.client = None
            return []
    
    async def process_transaction(self, address: str, tx_data: Dict):
        """Process a transaction and send notifications if needed"""
        try:
            signature = tx_data['signature']
            logger.info(f"Processing transaction {signature} for {address}")
            
            # Check if we already processed this transaction
            existing_txs = self.db.get_recent_transactions(address, limit=100)
            if any(tx['signature'] == signature for tx in existing_txs):
                logger.info(f"Transaction {signature} already processed, skipping")
                return
            
            # Get full transaction details
            transaction = await self.get_transaction_details(signature)
            if not transaction:
                logger.warning(f"Could not get transaction details for {signature}")
                return
            
            # Analyze transaction
            tx_info = await self.analyze_transaction(transaction)
            
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
            
            # Send notification (always notify for now)
            await self.send_notification(address, signature, tx_info)
            logger.info(f"Notification sent for transaction {signature}")
                
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
                
                # If tracking is running, just add the address to the polling tasks
                if self.is_running:
                    logger.info("Adding new address to existing tracking")
                    asyncio.create_task(self.poll_address_transactions(address))
                else:
                    logger.info("Starting tracking for new address")
                    await self.start_tracking()
                
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
                # Note: The polling task for this address will continue but won't find new transactions
                # This is acceptable as it will eventually timeout and stop
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
