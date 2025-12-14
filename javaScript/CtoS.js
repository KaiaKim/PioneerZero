//send action to websocket server

function sendMessage() {
    const input = document.getElementById('chat-input').value.trim();
    if (!input) return;
    const gameId = localStorage.getItem('game_id');
    if (!gameId) {
        console.error('No game_id found. Cannot send message.');
        return;
    }
    // It's best to format the message here, on the client side, so you control the display and parsing.
    // This way, the server can remain mostly message-agnostic and simply distribute the message.
    const message = {
        type: 'chat', // To let websocket.py (the server) know this message is a chat message, you should set a specific flag or type.
        sender: 'Pikita',
        content: input,
        game_id: gameId
    };

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
        document.getElementById('chat-input').value = '';
    } else {
        console.error('WebSocket not connected. Message not sent.');
    }
}

function startGame() {
    console.log("startGame Clicked");
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            action: 'start_game'
        };
        console.log("message is~~>>>", message);
        ws.send(JSON.stringify(message));
        console.log("startGame Executed");
        // loadGame() will be called after game is created and game_id is received

    } else {
        console.error('WebSocket not connected');
        connectWebSocket();
    }
    // viewMain() will be called when vomit_data is received in StoC.js
}

function loadGame() {
    const gameId = localStorage.getItem('game_id');
    if (ws && ws.readyState === WebSocket.OPEN && gameId) {
        const message = {
            action: 'load_game',
            game_id: gameId
        };
        ws.send(JSON.stringify(message));
    }
    
}

function endGame() {
    // End the game session
    const gameId = localStorage.getItem('game_id');
    if (ws && ws.readyState === WebSocket.OPEN && gameId) {
        const message = {
            action: 'end_game',
            game_id: gameId
        };
        ws.send(JSON.stringify(message));
        localStorage.removeItem('game_id'); // Clear game_id from localStorage
    }
    viewResults();
}
