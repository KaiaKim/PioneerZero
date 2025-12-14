// WebSocket connection
//(mostly) receive message from websocket server

let ws = null;

// Helper functions for game_id in localStorage
function getGameId() {
    return localStorage.getItem('game_id');
}

function setGameId(gameId) {
    if (gameId) {
        localStorage.setItem('game_id', gameId);
    } else {
        localStorage.removeItem('game_id');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
    
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                if (event.shiftKey) {
                    return;
                } else {
                    // Enter alone sends the message, prevent newline
                    event.preventDefault();
                    sendMessage();
                }
            }
        });
    }
});

function connectWebSocket() {
    const wsUrl = `ws://localhost:8000/ws`;
    ws = new WebSocket(wsUrl);
    // Generate or retrieve guest_id from localStorage
    let guest_id = localStorage.getItem('guest_id');
    if (!guest_id) {
        guest_id = crypto.randomUUID();
        localStorage.setItem('guest_id', guest_id);
    }

    ws.onopen = function() {
        console.log('WebSocket connected');
        // Send guest_id to server
        ws.send(JSON.stringify({
            action: 'authenticate',
            guest_id: guest_id
        }));
        loadGame();
        
    };
    
    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data); //str -> Javascript object
        if (msg.type === "game_created") {
            setGameId(msg.game_id);
            clearChat();
            loadGame();
        }
        else if (msg.type === "guest_assigned") {
            // Store guest_number in localStorage for display
            localStorage.setItem('guest_number', msg.guest_number);
            console.log(`You joined as Guest ${msg.guest_number}`);
            document.querySelector('#chat-char').textContent = `Guest ${msg.guest_number}`;
        }
        else if (msg.type === "vomit_data") {
            console.log('Game data received');
            viewMain();
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
            // If we only displayed messages locally in sendMessage(), we wouldn't see chats from other users.
            if (msg.sort === "user"){
            loadChat(msg.sender || "noname", msg.time, msg.content, false);
            }
            else if (msg.sort === "system"){
            loadChat("System", new Date().toLocaleTimeString(), msg.content, true);
            }
        }
        else if (msg.type === "no_game") {
            console.log('No active game found');
            viewSelection();
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = function(event) {
        console.log('WebSocket disconnected');
    };
}