document.addEventListener('DOMContentLoaded', function() {
    const menuBtn = document.querySelector('.menu-btn');
    const menuPanel = document.getElementById('menuPanel');
    const mainContent = document.getElementById('mainContent');
    let menuOpen = false;

    menuBtn.addEventListener('click', function() {
        menuOpen = !menuOpen;
        if (menuOpen) {
            menuPanel.style.left = '0';
            mainContent.style.marginLeft = '250px';
        } else {
            menuPanel.style.left = '-250px';
            mainContent.style.marginLeft = '0';
        }
    });

    const messageInput = document.getElementById('messageInput');
    const keys = document.querySelectorAll('.key');
    
    keys.forEach(key => {
        key.addEventListener('click', function() {
            const keyText = this.textContent;
            if (keyText === 'DELETE') {
                messageInput.value = messageInput.value.slice(0, -1);
            } else if (keyText === 'SPACE') {
                messageInput.value += ' ';
            } else {
                messageInput.value += keyText;
            }
            messageInput.focus();
        });
    });

    const sendBtn = document.querySelector('.send-btn');
    sendBtn.addEventListener('click', function() {
        if (messageInput.value.trim()) {
            messageInput.value = '';
        }
    });
});