document.addEventListener('DOMContentLoaded', function() {
    // Initialize session list display
    updateSessionListDisplay();
    
    // Connect to lobby WebSocket
    connectLobbyWebSocket();
});

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