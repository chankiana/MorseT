from flask import url_for

def get_js_content():
    """
    Returns the JavaScript content as a string that will be served by Flask
    """
    return """
document.addEventListener('DOMContentLoaded', function() {
    // Menu functionality
    const menuBtn = document.querySelector('.menu-btn');
    const menuPanel = document.getElementById('menuPanel');
    const mainContent = document.getElementById('mainContent');
    let menuOpen = false;

    menuBtn.addEventListener('click', function() {
        menuOpen = !menuOpen;
        // Send menu state to server
        fetch('/toggle_menu', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ menuOpen: menuOpen })
        });

        if (menuOpen) {
            menuPanel.style.left = '0';
            mainContent.style.marginLeft = '250px';
        } else {
            menuPanel.style.left = '-250px';
            mainContent.style.marginLeft = '0';
        }
    });

    // Virtual keyboard functionality
    const messageInput = document.getElementById('messageInput');
    const keys = document.querySelectorAll('.key');
    
    keys.forEach(key => {
        key.addEventListener('click', function() {
            const keyText = this.textContent;
            if (this.classList.contains('delete')) {
                messageInput.value = messageInput.value.slice(0, -1);
            } else if (this.classList.contains('space')) {
                messageInput.value += ' ';
            } else {
                messageInput.value += keyText;
            }
            messageInput.focus();
        });
    });

    // Message sending functionality
    const sendBtn = document.querySelector('.send-btn');
    sendBtn.addEventListener('click', function() {
        const message = messageInput.value.trim();
        if (message) {
            // Get selected vessel from menu
            const selectedVessel = document.querySelector('.vessel-btn.selected');
            const recipient = selectedVessel ? selectedVessel.textContent : null;

            // Send message to server
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    recipient: recipient
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    messageInput.value = '';
                    // Refresh messages
                    updateMessages(recipient);
                }
            });
        }
    });

    // Vessel selection functionality
    const vesselBtns = document.querySelectorAll('.vessel-btn');
    vesselBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            vesselBtns.forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            updateMessages(this.textContent);
        });
    });

    // Function to update messages
    function updateMessages(vessel) {
        const url = vessel ? 
            `/get_messages/${encodeURIComponent(vessel)}` : 
            '/get_messages';
        
        fetch(url)
            .then(response => response.json())
            .then(messages => {
                const chatArea = document.querySelector('.chat-area');
                chatArea.innerHTML = '';
                messages.forEach(message => {
                    const messageGroup = document.createElement('div');
                    messageGroup.className = 'message-group';
                    messageGroup.innerHTML = `
                        <div>${message.header}</div>
                        ${message.message_received === '[No Message Received]' ?
                            `<div class="message-received">[No Message Received]</div>` :
                            `<div class="message-content">${message.message_received}</div>`
                        }
                        ${message.message_sent ?
                            message.message_sent === '[No Message Sent]' ?
                                `<div class="message-sent">[No Message Sent]</div>` :
                                `<div class="message-response">Response: ${message.message_sent}</div>`
                            : ''
                        }
                        <div class="timestamp">${message.formatted_time}</div>
                    `;
                    chatArea.appendChild(messageGroup);
                });
            });
    }

    // Initial messages load
    updateMessages(null);
});
"""

# Flask route to serve the JavaScript
def setup_js_route(app):
    @app.route('/static/js/design.py')
    def serve_js():
        return get_js_content(), 200, {'Content-Type': 'text/javascript'}