document.addEventListener('DOMContentLoaded', function() {
    // Connect to lobby WebSocket (will trigger list_games and update display)
    connectLobbyWebSocket();
});

function updateSessionListDisplay(sessions) {
    // sessions is array of {game_id, player_count, status} from server
    const sessionList = document.getElementById('session-list');
    if (!sessionList) {
        // We're not in the lobby page, skip
        return;
    }
    
    // Clear existing list
    sessionList.innerHTML = '';
    
    if (!sessions || sessions.length === 0) {
        const emptyMsg = document.createElement('p');
        emptyMsg.textContent = 'No active game sessions. Click "New Game" to create one.';
        emptyMsg.style.color = '#666';
        emptyMsg.style.fontStyle = 'italic';
        sessionList.appendChild(emptyMsg);
        return;
    }
    
    // Create list items for each session
    sessions.forEach(session => {
        const gameId = session.game_id;
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