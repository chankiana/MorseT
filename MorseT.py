from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database_handler import MorseDBHandler
from static.js.design import setup_js_route
import os
import json
from datetime import datetime
from cryptography.fernet import Fernet
import bcrypt

def load_config():
    """Load the config file containing hashed passwords."""
    with open("config.json", "r") as file:
        config = json.load(file)
    return config

class FlaskMorseApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_fallback_key')  # Replace fallback with a secure value
        self.app.config['SESSION_TYPE'] = 'filesystem'
        setup_js_route(self.app)
        self.config = load_config()
        self.db = self.initialize_database()
        self.setup_routes()
    
    def initialize_database(self):
        """Initialize the database connection."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'SQLite Database', 'morse_decoder.db')
        return MorseDBHandler(db_path)
    
    def setup_routes(self):
        """Set up all Flask routes."""
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page."""
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                user_password_hash = self.config['users'].get(username)
                if user_password_hash and bcrypt.checkpw(password.encode(), user_password_hash.encode()):
                    # Successful login
                    session['user'] = username
                    return redirect(url_for('index'))
                else:
                    # Invalid login, pass a failure message to the template
                    return render_template('auth.html', error_message="Invalid credentials, please try again.")
            return render_template('auth.html')
        
        @self.app.route('/logout')
        def logout():
            """Logout route."""
            session.clear()
            return redirect(url_for('login'))
        
        @self.app.route('/')
        def index():
            """Main application page."""
            if 'user' not in session:
                return redirect(url_for('login'))

            messages = self.get_messages()
            vessels = self.db.get_unique_vessels()
            return render_template(
                'index.html', 
                messages=self.format_messages(messages), 
                vessels=vessels, 
                current_channel="All"
            )
        
        @self.app.route('/get_messages/<vessel>')
        def get_vessel_messages(vessel):
            """Get messages for a specific vessel."""
            if 'user' not in session:
                return redirect(url_for('login'))
            messages = self.db.get_messages(vessel_sender=vessel, vessel_recipient=None)
            return jsonify(self.format_messages(messages))
        
        @self.app.route('/get_messages')
        def get_all_messages():
            """Get all messages."""
            if 'user' not in session:
                return redirect(url_for('login'))
            messages = self.get_messages()
            return jsonify(self.format_messages(messages))
        
        @self.app.route('/send_message', methods=['POST'])
        def send_message():
            """Handle sending a message."""
            if 'user' not in session:
                return redirect(url_for('login'))
            data = request.json
            return jsonify({'status': 'success'})
        
        @self.app.route('/toggle_menu', methods=['POST'])
        def toggle_menu():
            """Handle menu toggle requests."""
            if 'user' not in session:
                return redirect(url_for('login'))
            return jsonify({'status': 'success'})
    
    def format_messages(self, messages):
        """Format messages to include clear sender/receiver information."""
        formatted_messages = []
        for msg in messages:
            formatted_msg = msg.copy()
            formatted_msg['header'] = f"From: {msg['vessel_sender']} To: {msg['vessel_recipient']}"
            formatted_msg['formatted_time'] = datetime.strptime(
                msg['timestamp'], '%Y-%m-%d %H:%M:%S'
            ).strftime('%Y-%m-%d %H:%M:%S')
            formatted_messages.append(formatted_msg)
        return formatted_messages
    
    def get_messages(self):
        """Retrieve all messages from the database."""
        messages = self.db.get_messages()
        messages.sort(key=lambda x: x['timestamp'])
        return messages
    
    def run(self, debug=True, host='0.0.0.0'):
        """Run the Flask application."""
        self.app.run(debug=debug, host=host)

if __name__ == '__main__':
    app = FlaskMorseApp()
    app.run(debug=True)
