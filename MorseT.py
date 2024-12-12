from flask import Flask, render_template, request, jsonify
from database_handler import MorseDBHandler
import os
from datetime import datetime

class FlaskMorseApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.db = self.initialize_database()
        self.setup_routes()
    
    def initialize_database(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'SQLite Database', 'morse_decoder.db')
        return MorseDBHandler(db_path)
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            messages = self.get_messages()
            vessels = self.db.get_unique_vessels()
            return render_template('index.html', 
                                messages=self.format_messages(messages), 
                                vessels=vessels, 
                                current_channel="All")
        
        @self.app.route('/get_messages/<vessel>')
        def get_vessel_messages(vessel):
            messages = self.db.get_messages(vessel_sender=vessel, vessel_recipient=None)
            return jsonify(self.format_messages(messages))
        
        @self.app.route('/get_messages')
        def get_all_messages():
            messages = self.get_messages()
            return jsonify(self.format_messages(messages))
        
        @self.app.route('/send_message', methods=['POST'])
        def send_message():
            data = request.json
            return jsonify({'status': 'success'})
        
        @self.app.route('/toggle_menu', methods=['POST'])
        def toggle_menu():
            return jsonify({'status': 'success'})
    
    def format_messages(self, messages):
        """Format messages to include clear sender/receiver information"""
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
        messages = self.db.get_messages()
        messages.sort(key=lambda x: x['timestamp'])
        return messages
    
    def run(self, debug=True):
        self.app.run(debug=debug)

if __name__ == '__main__':
    app = FlaskMorseApp()
    app.run(debug=True)