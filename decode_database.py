import os
import logging
from database_handler import MorseDBHandler
from datetime import datetime
from tabulate import tabulate  # for nice table formatting

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_decoder.log')
    ]
)

logger = logging.getLogger(__name__)

def get_database_path():
    """Get the path to the database file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'SQLite Database', 'morse_decoder.db')
        db_path = os.path.normpath(db_path)
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at: {db_path}")
            raise FileNotFoundError(f"Database file not found at: {db_path}")
            
        logger.debug(f"Database path: {db_path}")
        return db_path
    except Exception as e:
        logger.error(f"Error getting database path: {str(e)}")
        raise

def format_timestamp(timestamp_str):
    """Format timestamp string for better readability"""
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Error formatting timestamp {timestamp_str}: {str(e)}")
        return timestamp_str

def decode_messages(vessel_sender_filter=None, vessel_recipient_filter=None):
    """
    Decode and display all messages from the database
    
    Args:
        vessel_sender_filter (str, optional): Filter messages by sender vessel name
        vessel_recipient_filter (str, optional): Filter messages by recipient vessel name
    """
    try:
        logger.info("Starting database message decoding")
        
        # Initialize database handler
        db_path = get_database_path()
        db = MorseDBHandler(db_path)
        
        # Get messages
        messages = db.get_messages(vessel_sender_filter, vessel_recipient_filter)
        
        if not messages:
            logger.info("No messages found in database")
            print("\nNo messages found in database.")
            return
        
        # Prepare table headers and rows
        headers = ['ID', 'Vessel Sender', 'Vessel Recipient', 'Message Received', 'Message Sent', 'Timestamp']
        rows = []
        
        for msg in messages:
            rows.append([
                msg['id'],
                msg['vessel_sender'],
                msg['vessel_recipient'],
                msg['message_received'],
                msg['message_sent'],
                format_timestamp(msg['timestamp'])
            ])
        
        # Print summary
        print(f"\nFound {len(messages)} message(s)")
        if vessel_sender_filter:
            print(f"Filtered by sender vessel: {vessel_sender_filter}")
        if vessel_recipient_filter:
            print(f"Filtered by recipient vessel: {vessel_recipient_filter}")
            
        # Print table
        print("\n" + tabulate(rows, headers=headers, tablefmt='grid'))
        
        logger.info(f"Successfully decoded {len(messages)} messages")
        
    except FileNotFoundError as e:
        logger.error("Database file not found")
        print(f"\nError: {str(e)}")
    except Exception as e:
        logger.error(f"Error decoding messages: {str(e)}", exc_info=True)
        print(f"\nError: An unexpected error occurred: {str(e)}")

def main():
    """Main function with interactive menu"""
    print("\nMorse Code Database Decoder")
    print("==========================")
    
    while True:
        print("\nOptions:")
        print("1. View all messages")
        print("2. Filter by vessel sender")
        print("3. Filter by vessel recipient")
        print("4. Filter by both vessel sender and recipient")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            decode_messages()
        elif choice == '2':
            vessel_sender = input("Enter vessel sender name to filter: ").strip()
            decode_messages(vessel_sender_filter=vessel_sender)
        elif choice == '3':
            vessel_recipient = input("Enter vessel recipient name to filter: ").strip()
            decode_messages(vessel_recipient_filter=vessel_recipient)
        elif choice == '4':
            vessel_sender = input("Enter vessel sender name to filter: ").strip()
            vessel_recipient = input("Enter vessel recipient name to filter: ").strip()
            decode_messages(vessel_sender_filter=vessel_sender, vessel_recipient_filter=vessel_recipient)
        elif choice == '5':
            logger.info("Program terminated by user")
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
        print("\nProgram terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}", exc_info=True)
        print(f"\nAn unexpected error occurred: {str(e)}")
