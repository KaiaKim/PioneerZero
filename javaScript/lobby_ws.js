// Lobby WebSocket connection
let lobbyWs = null;

function connectLobbyWebSocket() {
    const wsUrl = `ws://localhost:8000/ws`;
    lobbyWs = new WebSocket(wsUrl);
    
    // Generate or retrieve guest_id from localStorage
    let guest_id = localStorage.getItem('guest_id');
    if (!guest_id) {
        guest_id = crypto.randomUUID();
        localStorage.setItem('guest_id', guest_id);
    }

    lobbyWs.onopen = function() {
        console.log('Lobby WebSocket connected');
        // Send guest_id to server
        lobbyWs.send(JSON.stringify({
            action: 'authenticate',
            guest_id: guest_id
        }));
    };
    
    lobbyWs.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        
        if (msg.type === "game_created") {
            const gameId = msg.game_id;
            setGameId(gameId);
            // Add session to lobby list
            addSessionToList(gameId);
        }
        else if (msg.type === "guest_assigned") {
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
        console.error('Lobby WebSocket not connected');
        connectLobbyWebSocket();
    }
}
