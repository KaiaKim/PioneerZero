// Store active sessions in memory (for lobby display)
let activeSessions = [];

function addSessionToList(gameId) {
    // Check if session already exists in list
    if (activeSessions.includes(gameId)) {
        return;
    }
    
    activeSessions.push(gameId);
    updateSessionListDisplay();
}

function removeSessionFromList(gameId) {
    activeSessions = activeSessions.filter(id => id !== gameId);
    updateSessionListDisplay();
}

function updateSessionListDisplay() {
    const sessionList = document.getElementById('session-list');
    if (!sessionList) {
        // We're not in the lobby page, skip
        return;
    }
    
    // Clear existing list
    sessionList.innerHTML = '';
    
    if (activeSessions.length === 0) {
        const emptyMsg = document.createElement('p');
        emptyMsg.textContent = 'No active game sessions. Click "New Game" to create one.';
        emptyMsg.style.color = '#666';
        emptyMsg.style.fontStyle = 'italic';
        sessionList.appendChild(emptyMsg);
        return;
    }
    
    // Create list items for each session
    activeSessions.forEach(gameId => {
        const sessionItem = document.createElement('div');
        sessionItem.classList.add('session-item');
        sessionItem.dataset.gameId = gameId;
        // Make entire item clickable
        sessionItem.style.cursor = 'pointer';
        sessionItem.onclick = function() {
            openGameRoom(gameId);
        };
        
        const thumb = document.createElement('div');
        thumb.classList.add('session-thumb');
        thumb.textContent = 'Preview';
        
        const sessionId = document.createElement('span');
        sessionId.classList.add('session-id');
        sessionId.textContent = `Game: ${gameId}`;
        
        const joinButton = document.createElement('button');
        joinButton.classList.add('join-button');
        joinButton.textContent = 'Join';
        joinButton.onclick = function(e) {
            e.stopPropagation(); // Prevent double-trigger from parent click
            openGameRoom(gameId);
        };
        
        sessionItem.appendChild(thumb);
        sessionItem.appendChild(sessionId);
        sessionItem.appendChild(joinButton);
        sessionList.appendChild(sessionItem);
    });
}

function openGameRoom(gameId) {
    // Open room.html in a new tab with game_id as URL parameter
    const roomUrl = `room.html?game_id=${gameId}`;
    window.open(roomUrl, '_blank');
}

function viewResults() {
    document.querySelector('.floor-3d').style.display = 'none';
    document.querySelector('.results-container').style.display = 'block';
}

function clearChat(){
    const chatLog = document.getElementById('chat-log');
    if (chatLog) {
        chatLog.innerHTML = '';
    }
}

function loadChat(sender, time, content, isSystem) {
    const chatLog = document.getElementById('chat-log');
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    if (isSystem) {
        messageDiv.classList.add('system');
    }
    
    const headerDiv = document.createElement('div');
    headerDiv.classList.add('chat-message-header');
    
    const nameSpan = document.createElement('span');
    nameSpan.classList.add('chat-message-name');
    nameSpan.textContent = sender;
    
    const timeSpan = document.createElement('span');
    timeSpan.classList.add('chat-message-time');
    timeSpan.textContent = time;
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('chat-message-content');
    contentDiv.textContent = content;
    
    headerDiv.appendChild(nameSpan);
    headerDiv.appendChild(timeSpan);
    messageDiv.appendChild(headerDiv);
    messageDiv.appendChild(contentDiv);
    
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function loadTokens(characters) {
    // Remove all elements with the 'token' class from the DOM
    document.querySelectorAll('.token').forEach(token => token.remove());
    // Create new tokens for each character
    characters.forEach(character => {
        const cellId = character.pos;
        const cell = Array.from(document.querySelectorAll('.cell')).find(c => c.textContent.trim() === cellId);

        const token = document.createElement('img');
        token.alt = character.name;
        token.src = character.token_image;
        token.classList.add('token');
        cell.appendChild(token);
    });
}
