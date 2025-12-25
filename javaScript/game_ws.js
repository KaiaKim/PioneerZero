// Game WebSocket connection
let gameWs = null;

function connectGameWebSocket() {
    const wsUrl = `ws://localhost:8000/ws`; //change later
    gameWs = new WebSocket(wsUrl);
    
    let guest_id = getGuestId();

    gameWs.onopen = function() {
        console.log('Game WebSocket connected');
        authenticateGuest(guest_id, gameWs);
        
        // Join and load game if we have a game_id
        const gameId = getGameId();
        if (gameId) {
            joinGame(gameId); 
        }
    };
    
    gameWs.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        
        if (msg.type === "guest_assigned") {
            // Store guest_number in localStorage for display
            localStorage.setItem('guest_number', msg.guest_number);
            console.log(`You joined as Guest ${msg.guest_number}`);
            const chatChar = document.querySelector('#chat-char');
            if (chatChar) {
                chatChar.textContent = `Guest ${msg.guest_number}`;
            }
        }
        else if (msg.type === "joined_game") {
            // Successfully joined game, now load it
            loadGame();
        }
        else if (msg.type === "join_failed") {
            console.error('Failed to join game:', msg.message);
        }
        else if (msg.type === "vomit_data") {
            console.log('Game data received');
            document.getElementById('vomit-box').value = JSON.stringify(msg, null, 2);
            loadTokens(msg.characters);
        }
        else if (msg.type === "chat_history") {
            // Load all chat history messages
            msg.messages.forEach(chatMsg => {
                if (chatMsg.sort === "user") {
                    loadChat(chatMsg.sender || "noname", chatMsg.time, chatMsg.content, false);
                } else if (chatMsg.sort === "system") {
                    loadChat("System", chatMsg.time, chatMsg.content, true);
                }
            });
        }
        else if (msg.type === "chat") {
            // We handle user_chat here so that messages from ALL users (not just this client) are displayed in real-time.
            if (msg.sort === "user"){
                loadChat(msg.sender || "noname", msg.time, msg.content, false);
            }
            else if (msg.sort === "system"){
                loadChat("System", new Date().toLocaleTimeString(), msg.content, true);
            }
        }
        else if (msg.type === "no_game") {
            console.log('No active game found');
        }
    };

    gameWs.onerror = function(error) {
        console.error('Game WebSocket error:', error);
    };
    
    gameWs.onclose = function(event) {
        console.log('Game WebSocket disconnected');
    };
}

function joinGame(gameId) {
    if (gameWs && gameWs.readyState === WebSocket.OPEN && gameId) {
        const message = {
            action: 'join_game',
            game_id: gameId
        };
        gameWs.send(JSON.stringify(message));
    }
}

function loadGame() {
    const gameId = getGameId();
    if (gameWs && gameWs.readyState === WebSocket.OPEN && gameId) {
        const message = {
            action: 'load_game',
            game_id: gameId
        };
        gameWs.send(JSON.stringify(message));
    }
}

function endGame() {
    // End the game session
    const gameId = getGameId();
    if (gameWs && gameWs.readyState === WebSocket.OPEN && gameId) {
        const message = {
            action: 'end_game',
            game_id: gameId
        };
        gameWs.send(JSON.stringify(message));
        localStorage.removeItem('game_id'); // Clear game_id from localStorage
    }
}

function sendMessage() {
    const input = document.getElementById('chat-input').value.trim();
    if (!input) return;
    const gameId = getGameId();
    if (!gameId) {
        console.error('No game_id found. Cannot send message.');
        return;
    }
    const message = {
        action: 'chat',
        sender: `Guest ${localStorage.getItem('guest_number')}`,
        content: input,
        game_id: gameId
    };

    if (gameWs && gameWs.readyState === WebSocket.OPEN) {
        gameWs.send(JSON.stringify(message));
        document.getElementById('chat-input').value = '';
    } else {
        console.error('Game WebSocket not connected. Message not sent.');
    }
}
