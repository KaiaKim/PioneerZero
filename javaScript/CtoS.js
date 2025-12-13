//send action to websocket server

function sendMessage() {
    const input = document.getElementById('chat-input').value.trim();
    if (!input) return;
    // It's best to format the message here, on the client side, so you control the display and parsing.
    // This way, the server can remain mostly message-agnostic and simply distribute the message.
    const message = {
        type: 'chat', // To let websocket.py (the server) know this message is a chat message, you should set a specific flag or type.
        sender: 'Pikita',
        content: input
    };

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
        document.getElementById('chat-input').value = '';
    } else {
        console.error('WebSocket not connected. Message not sent.');
    }
}

function startGame() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            action: 'start_game'
        };
        ws.send(JSON.stringify(message));
        loadGame();
    } else {
        console.error('WebSocket not connected');
        connectWebSocket();
    }
    // viewMain() will be called when vomit_data is received in StoC.js
}

function loadGame() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            action: 'load_game'
        };
        ws.send(JSON.stringify(message));
    }
    
}

function endGame() {
    // End the game session
    if (ws && ws.readyState === WebSocket.OPEN && currentSessionId) {
        const message = {
            action: 'end_game',
            session_id: currentSessionId
        };
        ws.send(JSON.stringify(message));
        currentSessionId = null; // Clear session ID
    }
    viewResults();
}
