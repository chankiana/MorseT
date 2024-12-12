# database_handler.py
import sqlite3
from cryptography.fernet import Fernet, InvalidToken
import os
import logging
from datetime import datetime

class MorseDBHandler:
    # Predefined static encryption key
    PREDEFINED_KEY = b'd99vdna1RPR21BrXlXL5CVVSQVVAEsLqXgNU22v_Xwk='

    def __init__(self, db_path):
        """Initialize database handler with encryption"""
        self.db_path = os.path.abspath(os.path.normpath(db_path))
        self.db_dir = os.path.dirname(self.db_path)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing database handler for path: {self.db_path}")
        
        # Setup encryption and database
        self._setup_encryption()
        self._setup_database()
    
    def _setup_encryption(self):
        """Set up encryption with a predefined static key"""
        try:
            self.cipher_suite = Fernet(self.PREDEFINED_KEY)
            self.logger.debug("Encryption setup completed successfully")
        except Exception as e:
            self.logger.error(f"Error setting up encryption: {str(e)}")
            raise
    
    def _setup_database(self):
        """Initialize database and create table if needed"""
        try:
            self.logger.debug(f"Creating database directory: {self.db_dir}")
            os.makedirs(self.db_dir, exist_ok=True)
            
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                
                self.logger.debug("Creating messages table if not exists")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vessel_sender TEXT NOT NULL,
                        vessel_recipient TEXT NOT NULL,
                        message_received TEXT,
                        message_sent TEXT,
                        timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database setup completed successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database setup error: {str(e)}")
            raise
    
    def encrypt_message(self, message):
        """Encrypt a message with error handling"""
        try:
            if not message:
                self.logger.warning("Attempted to encrypt empty message")
                return None
                
            encrypted = self.cipher_suite.encrypt(message.encode())
            self.logger.debug("Message encrypted successfully")
            return encrypted.decode()
            
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            return None
    
    def decrypt_message(self, encrypted_message):
        """Decrypt a message with error handling"""
        try:
            if not encrypted_message:
                self.logger.warning("Attempted to decrypt empty or NULL message")
                return None  # Return None for empty messages

            decrypted = self.cipher_suite.decrypt(encrypted_message.encode())
            self.logger.debug("Message decrypted successfully")
            return decrypted.decode()

        except InvalidToken:
            self.logger.warning("Invalid token encountered during decryption")
            return "[Decryption Failed]"
        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            return "[Decryption Error]"

    
    def save_message(self, vessel_sender, vessel_recipient, message_received, message_sent):
        """Save an encrypted message to database"""
        self.logger.info(f"Attempting to save message from vessel: {vessel_sender} to {vessel_recipient}")
        
        # Ensure sender and recipient are provided
        if not vessel_sender or not vessel_recipient:
            self.logger.warning("Empty vessel sender or recipient provided")
            return False
        
        try:
            # Encrypt the messages if they are not None
            encrypted_received = self.encrypt_message(message_received.strip()) if message_received else None
            encrypted_sent = self.encrypt_message(message_sent.strip()) if message_sent else None
            
            # Save to database with explicit transaction
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                
                cursor.execute('BEGIN TRANSACTION')
                
                try:
                    cursor.execute('''
                        INSERT INTO messages (vessel_sender, vessel_recipient, message_received, message_sent)
                        VALUES (?, ?, ?, ?)
                    ''', (vessel_sender, vessel_recipient, encrypted_received, encrypted_sent))
                    
                    # Verify the insertion
                    cursor.execute('SELECT changes()')
                    if cursor.fetchone()[0] == 1:
                        conn.commit()
                        self.logger.info(f"Message saved successfully from {vessel_sender} to {vessel_recipient}")
                        return True
                    else:
                        conn.rollback()
                        self.logger.warning("No changes made to database")
                        return False
                        
                except sqlite3.Error as e:
                    conn.rollback()
                    self.logger.error(f"Database error in transaction: {str(e)}")
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error while saving: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error saving message: {str(e)}")
            return False

    
    def get_messages(self, vessel_sender=None, vessel_recipient=None, limit=100):
        """
        Retrieve and decrypt messages from database.
        """
        self.logger.info(f"Retrieving messages for sender: {vessel_sender} and recipient: {vessel_recipient}")

        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                query = 'SELECT id, vessel_sender, vessel_recipient, message_received, message_sent, timestamp FROM messages '
                conditions = []
                params = []

                if vessel_sender:
                    conditions.append("vessel_sender = ?")
                    params.append(vessel_sender)
                if vessel_recipient:
                    conditions.append("vessel_recipient = ?")
                    params.append(vessel_recipient)

                if conditions:
                    query += "WHERE " + " AND ".join(conditions)
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, tuple(params))
                messages = []
                for row in cursor.fetchall():
                    try:
                        decrypted_received = self.decrypt_message(row[3]) or "[No Message Received]"
                        decrypted_sent = self.decrypt_message(row[4]) or "[No Message Sent]"
                        messages.append({
                            'id': row[0],
                            'vessel_sender': row[1],
                            'vessel_recipient': row[2],
                            'message_received': decrypted_received,
                            'message_sent': decrypted_sent,
                            'timestamp': row[5]
                        })
                        self.logger.debug(f"Successfully processed message ID: {row[0]}")
                    except Exception as e:
                        self.logger.error(f"Error processing message ID {row[0]}: {str(e)}")
                        continue

                self.logger.info(f"Retrieved {len(messages)} messages successfully")
                return messages
        except sqlite3.Error as e:
            self.logger.error(f"Database error while retrieving messages: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {str(e)}")
            raise

    
    def clear_database(self):
        """Clear all messages from database - useful for testing"""
        self.logger.warning("Attempting to clear entire database")
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM messages')
                conn.commit()
                self.logger.info("Database cleared successfully")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error clearing database: {str(e)}")
            return False
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute('SELECT COUNT(*) FROM messages')
                total_count = cursor.fetchone()[0]
                
                # Get count per sender
                cursor.execute('''
                    SELECT vessel_sender, COUNT(*) 
                    FROM messages 
                    GROUP BY vessel_sender
                ''')
                sender_counts = dict(cursor.fetchall())
                
                # Get date range
                cursor.execute('''
                    SELECT MIN(timestamp), MAX(timestamp) 
                    FROM messages
                ''')
                date_range = cursor.fetchone()
                
                stats = {
                    'total_messages': total_count,
                    'sender_counts': sender_counts,
                    'first_message': date_range[0] if date_range[0] else None,
                    'last_message': date_range[1] if date_range[1] else None
                }
                
                self.logger.info("Statistics retrieved successfully")
                return stats
        except sqlite3.Error as e:
            self.logger.error(f"Error getting statistics: {str(e)}")
            return None

    def test_connection(self):
        """Test database connection"""
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                result = cursor.fetchone()[0] == 1
                self.logger.debug("Database connection test successful")
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            return False
        
    def execute_query(self, query, params=()):
        """Execute a query on the database and return the result."""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute(query, params)  # Execute the query with the provided parameters
        result = cursor.fetchall()  # Fetch all results
        connection.close()  # Close the connection
        return result

    def get_unique_vessels(self):
        query = "SELECT DISTINCT vessel_sender FROM messages"
        result = self.execute_query(query)
        return [row[0] for row in result]  

