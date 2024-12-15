from flask import url_for

def get_js_content():
    """
    Returns the JavaScript content as a string that will be served by Flask
    """
    return """
document.addEventListener('DOMContentLoaded', function() {

    const EMERGENCY_KEYWORDS = ['SOS', 'MAYDAY'];
    const WARNING_KEYWORDS = ['WARNING', 'REQUESTING ASSISTANCE'];

    function applyMessageHighlighting(messageElement, messageText) {
    const upperText = messageText.toUpperCase();
    
    if (EMERGENCY_KEYWORDS.some(keyword => upperText.includes(keyword))) {
        messageElement.classList.add('emergency');
    } else if (WARNING_KEYWORDS.some(keyword => upperText.includes(keyword))) {
        messageElement.classList.add('warning');
    }
}

    function updateMessages(vessel) {
        const url = vessel && vessel !== 'All' ? 
            `/get_messages/${encodeURIComponent(vessel)}` : 
            '/get_messages';
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const chatArea = document.querySelector('.chat-area');
                chatArea.innerHTML = '';
                
                const messages = Array.isArray(data) ? data : data.messages;
                
                messages.reverse().forEach(message => {
                    const messageGroup = document.createElement('div');
                    messageGroup.className = 'message-group';
                    
                    let messageHTML = '';
                    
                    if (message.message_received !== '[No Message Received]') {
                        const receivedDiv = document.createElement('div');
                        receivedDiv.className = 'message-bubble message-received';
                        receivedDiv.textContent = message.message_received;
                        applyMessageHighlighting(receivedDiv, message.message_received);
                        messageHTML += receivedDiv.outerHTML;
                    }
                    
                    if (message.message_sent && message.message_sent !== '[No Message Sent]') {
                        const sentDiv = document.createElement('div');
                        if (message.message_received !== '[No Message Received]') {
                            sentDiv.textContent = `Response: ${message.message_sent}`;
                        } else {
                            sentDiv.textContent = message.message_sent;
                        }
                        sentDiv.className = 'message-bubble message-sent';
                        applyMessageHighlighting(sentDiv, message.message_sent);
                        messageHTML += sentDiv.outerHTML;
                    }
                    
                    messageHTML += `<div class="timestamp ${message.message_sent && message.message_sent != '[No Message Sent]' ? 'timestamp-sent' : 'timestamp-received'}">${message.formatted_time}</div>`;
                    
                    messageGroup.innerHTML = messageHTML;
                    chatArea.appendChild(messageGroup);
                });
                
                chatArea.scrollTop = chatArea.scrollHeight;
            });
    }
    
    document.querySelectorAll('.quick-msg-btn').forEach(btn => {
    const buttonText = btn.textContent.toUpperCase();
    if (EMERGENCY_KEYWORDS.some(keyword => buttonText === keyword)) {
        btn.classList.add('emergency');
    } else if (WARNING_KEYWORDS.some(keyword => buttonText === keyword)) {
        btn.classList.add('warning');
    }
    });

    // Menu functionality
    const menuBtn = document.querySelector('.menu-btn');
    const menuPanel = document.getElementById('menuPanel');
    const mainContent = document.getElementById('mainContent');
    const currentChannelDisplay = document.getElementById('currentChannel');
    let menuOpen = false;

    // Panel expansion functionality
    const expandBtn = document.getElementById('expandBtn');
    const expandedPanel = document.getElementById('expandedPanel');
    const quickMsgBtns = document.querySelectorAll('.quick-msg-btn');
    const messageInput = document.getElementById('messageInput');
    let isPanelOpen = false;

    // Menu button click handler
    menuBtn.addEventListener('click', function(event) {
        event.stopPropagation();
        menuOpen = !menuOpen;
        
        menuPanel.classList.toggle('active');
        mainContent.classList.toggle('shifted');
        
        fetch('/toggle_menu', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ menuOpen: menuOpen })
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (menuOpen && 
            !menuPanel.contains(event.target) && 
            !menuBtn.contains(event.target)) {
            menuOpen = false;
            menuPanel.classList.remove('active');
            mainContent.classList.remove('shifted');
            
            fetch('/toggle_menu', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ menuOpen: false })
            });
        }
    });

    // Expand panel button click handler
    expandBtn.addEventListener('click', function(event) {
        event.stopPropagation();
        isPanelOpen = !isPanelOpen;
        expandedPanel.style.display = isPanelOpen ? 'block' : 'none';
        this.classList.toggle('active');
    });

    // Quick message button functionality
    quickMsgBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            messageInput.value = this.textContent;
            messageInput.focus();
            // Close the panel after selection
            isPanelOpen = false;
            expandedPanel.style.display = 'none';
            expandBtn.classList.remove('active');
        });
    });

    // Close panel when clicking outside
    document.addEventListener('click', function(event) {
        if (isPanelOpen && 
            !expandedPanel.contains(event.target) && 
            !expandBtn.contains(event.target)) {
            isPanelOpen = false;
            expandedPanel.style.display = 'none';
            expandBtn.classList.remove('active');
        }
    });

    // Virtual keyboard functionality
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
            const selectedVessel = document.querySelector('.vessel-btn.selected');
            const recipient = selectedVessel ? selectedVessel.getAttribute('data-vessel') : null;

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
                    updateMessages(recipient);
                }
            });
        }
    });

    // Enter key functionality
    messageInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendBtn.click();
        }
    });

    // Vessel selection functionality
    const vesselBtns = document.querySelectorAll('.vessel-btn');
    vesselBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            vesselBtns.forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            
            const vesselName = this.getAttribute('data-vessel');
            currentChannelDisplay.textContent = vesselName;
            
            updateMessages(vesselName);
            
            if (window.innerWidth <= 768) {
                menuOpen = false;
                menuPanel.classList.remove('active');
                mainContent.classList.remove('shifted');
            }
        });
    });

    // Function to update messages
    function updateMessages(vessel) {
        const url = vessel && vessel !== 'All' ? 
            `/get_messages/${encodeURIComponent(vessel)}` : 
            '/get_messages';
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const chatArea = document.querySelector('.chat-area');
                chatArea.innerHTML = '';
                
                const messages = Array.isArray(data) ? data : data.messages;
                
                messages.reverse().forEach(message => {
                    const messageGroup = document.createElement('div');
                    messageGroup.className = 'message-group';
                    
                    let messageHTML = '';
                    
                    if (message.message_received !== '[No Message Received]') {
                        messageHTML += `<div class="message-bubble message-received">${message.message_received}</div>`;
                    }
                    
                    if (message.message_sent && message.message_sent !== '[No Message Sent]') {
                        if (message.message_received !== '[No Message Received]') {
                            messageHTML += `<div class="message-bubble message-sent">Response: ${message.message_sent}</div>`;
                        } else {
                            messageHTML += `<div class="message-bubble message-sent">${message.message_sent}</div>`;
                        }
                    }
                    
                    messageHTML += `<div class="timestamp ${message.message_sent && message.message_sent != '[No Message Sent]' ? 'timestamp-sent' : 'timestamp-received'}">${message.formatted_time}</div>`;
                    
                    messageGroup.innerHTML = messageHTML;
                    chatArea.appendChild(messageGroup);
                });
                
                chatArea.scrollTop = chatArea.scrollHeight;
            });
    }

    // Set initial channel and load messages
    const initialChannel = currentChannelDisplay.textContent || 'All';
    const initialVesselBtn = document.querySelector(`.vessel-btn[data-vessel="${initialChannel}"]`);
    if (initialVesselBtn) {
        initialVesselBtn.classList.add('selected');
    }
    updateMessages(initialChannel);

    // Window resize handler
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            mainContent.classList.toggle('shifted', menuOpen);
        } else {
            mainContent.classList.remove('shifted');
        }
    });
});
"""

def setup_js_route(app):
    """Setup the JavaScript route for Flask"""
    @app.route('/static/js/design.js')
    def serve_js():
        return get_js_content(), 200, {'Content-Type': 'text/javascript'}