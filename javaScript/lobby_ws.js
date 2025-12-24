// Lobby WebSocket connection
let lobbyWs = null;

function connectLobbyWebSocket() {
    const wsUrl = `ws://localhost:8000/ws`;
    lobbyWs = new WebSocket(wsUrl);

    let guest_id = getGuestId() || genGuestId();

    lobbyWs.onopen = function() {
        console.log('Lobby WebSocket connected');
        authenticateGuest(guest_id, lobbyWs);
        listGames();
    };
    
    lobbyWs.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        
        if (msg.type === "game_created") {
            const gameId = msg.game_id;
            setGameId(gameId);
            // Re-request the list from server to ensure consistency
            listGames();
        }
        else if (msg.type === "list_games") {
            // Render directly from server response - no need to store in client state
            updateSessionListDisplay(msg.sessions);
        }

        
        if (msg.type === "guest_assigned") {
            // Store guest_number in localStorage for display
            localStorage.setItem('guest_number', msg.guest_number);
            console.log(`You joined as Guest ${msg.guest_number}`);
        }
    };

    lobbyWs.onerror = function(error) {
        console.error('Lobby WebSocket error:', error);
    };
    
    lobbyWs.onclose = function(event) {
        console.log('Lobby WebSocket disconnected');
    };
}

function createGame() {
    if (lobbyWs && lobbyWs.readyState === WebSocket.OPEN) {
        const message = {
            action: 'create_game'
        };
        lobbyWs.send(JSON.stringify(message));
    } else {
        console.error('Lobby WebSocket not connected 1');
        connectLobbyWebSocket();
    }
}

function listGames() {
    if (lobbyWs && lobbyWs.readyState === WebSocket.OPEN) {
        const message = {
            action: 'list_games'
        };
        lobbyWs.send(JSON.stringify(message));
    } else {
        console.error('Lobby WebSocket not connected 2');
        connectLobbyWebSocket();
    }
}

