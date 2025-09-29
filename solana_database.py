import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SolanaDatabase:
    def __init__(self, db_path: str = "solana_tracking.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table for tracked addresses
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracked_addresses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT UNIQUE NOT NULL,
                        nickname TEXT,
                        added_by TEXT NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Table for transaction history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT NOT NULL,
                        signature TEXT UNIQUE NOT NULL,
                        transaction_type TEXT,
                        amount REAL,
                        token_mint TEXT,
                        timestamp TIMESTAMP,
                        block_time INTEGER,
                        slot INTEGER,
                        FOREIGN KEY (address) REFERENCES tracked_addresses (address)
                    )
                ''')
                
                # Table for notification settings
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT NOT NULL,
                        min_amount REAL DEFAULT 0,
                        notification_types TEXT DEFAULT 'all',
                        discord_channel_id INTEGER,
                        FOREIGN KEY (address) REFERENCES tracked_addresses (address)
                    )
                ''')
                
                conn.commit()
                logger.info("Solana database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_tracked_address(self, address: str, nickname: str = None, added_by: str = "system") -> bool:
        """Add a new address to track"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tracked_addresses (address, nickname, added_by)
                    VALUES (?, ?, ?)
                ''', (address, nickname, added_by))
                conn.commit()
                logger.info(f"Added tracked address: {address}")
                return True
        except Exception as e:
            logger.error(f"Error adding tracked address: {e}")
            return False
    
    def remove_tracked_address(self, address: str) -> bool:
        """Remove an address from tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE tracked_addresses SET is_active = 0 WHERE address = ?', (address,))
                conn.commit()
                logger.info(f"Removed tracked address: {address}")
                return True
        except Exception as e:
            logger.error(f"Error removing tracked address: {e}")
            return False
    
    def get_tracked_addresses(self) -> List[Dict]:
        """Get all active tracked addresses"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT address, nickname, added_by, added_at 
                    FROM tracked_addresses 
                    WHERE is_active = 1
                ''')
                rows = cursor.fetchall()
                return [
                    {
                        'address': row[0],
                        'nickname': row[1],
                        'added_by': row[2],
                        'added_at': row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting tracked addresses: {e}")
            return []
    
    def add_transaction(self, address: str, signature: str, transaction_type: str, 
                       amount: float = None, token_mint: str = None, 
                       block_time: int = None, slot: int = None) -> bool:
        """Add a transaction to history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO transaction_history 
                    (address, signature, transaction_type, amount, token_mint, block_time, slot)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (address, signature, transaction_type, amount, token_mint, block_time, slot))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
    
    def get_recent_transactions(self, address: str = None, limit: int = 50) -> List[Dict]:
        """Get recent transactions for an address or all addresses"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if address:
                    cursor.execute('''
                        SELECT address, signature, transaction_type, amount, token_mint, 
                               timestamp, block_time, slot
                        FROM transaction_history 
                        WHERE address = ?
                        ORDER BY block_time DESC 
                        LIMIT ?
                    ''', (address, limit))
                else:
                    cursor.execute('''
                        SELECT address, signature, transaction_type, amount, token_mint, 
                               timestamp, block_time, slot
                        FROM transaction_history 
                        ORDER BY block_time DESC 
                        LIMIT ?
                    ''', (limit,))
                
                rows = cursor.fetchall()
                return [
                    {
                        'address': row[0],
                        'signature': row[1],
                        'transaction_type': row[2],
                        'amount': row[3],
                        'token_mint': row[4],
                        'timestamp': row[5],
                        'block_time': row[6],
                        'slot': row[7]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return []
    
    def set_notification_settings(self, address: str, min_amount: float = 0, 
                                 notification_types: str = "all", 
                                 discord_channel_id: int = None) -> bool:
        """Set notification settings for an address"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO notification_settings 
                    (address, min_amount, notification_types, discord_channel_id)
                    VALUES (?, ?, ?, ?)
                ''', (address, min_amount, notification_types, discord_channel_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting notification settings: {e}")
            return False
    
    def get_notification_settings(self, address: str) -> Optional[Dict]:
        """Get notification settings for an address"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT min_amount, notification_types, discord_channel_id
                    FROM notification_settings 
                    WHERE address = ?
                ''', (address,))
                row = cursor.fetchone()
                if row:
                    return {
                        'min_amount': row[0],
                        'notification_types': row[1],
                        'discord_channel_id': row[2]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            return None
