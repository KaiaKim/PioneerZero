// WebSocket connection
let ws = null;
let currentSessionId = null;

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
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        const message = {
            action: 'load_game'
        };

        ws.send(JSON.stringify(message));
    };
    
    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data); //str -> Javascript object

        if (msg.type === "vomit_data") {
            console.log('Game data received');
            // Store session_id when game data is received (either from start_game or load_game)
            if (msg.session_id) {
                currentSessionId = msg.session_id;
            }
            viewGame();
            document.getElementById('vomit-box').value = JSON.stringify(msg, null, 2);
            loadTokens(msg.characters);

        } else if (msg.type === "no_session") {
            console.log('No active session found');
            viewSelection();
        } else if (msg.type === "chat_history") {
            // Load all historical messages into chat log
            if (msg.messages && Array.isArray(msg.messages)) {
                msg.messages.forEach(message => {
                    loadChat(message.sender, message.time, message.content, message.message_type === "system_message");
            });
    }
        }
         else if (msg.type === "user_chat") {
            // We handle user_chat here so that messages from ALL users (not just this client) are displayed in real-time.
            // If we only displayed messages locally in sendMessage(), we wouldn't see chats from other users.
            loadChat(msg.sender || "noname", msg.time, msg.content, false);

        } else if (msg.type === "system_message") {
            loadChat("System", new Date().toLocaleTimeString(), msg.content, true);
        }
    };

    
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
    };
}

function sendMessage() {
    const input = document.getElementById('chat-input').value.trim();
    if (!input) return;
    // It's best to format the message here, on the client side, so you control the display and parsing.
    // This way, the server can remain mostly message-agnostic and simply distribute the message.
    const message = {
        type: 'user_chat', // To let websocket.py (the server) know this message is a chat message, you should set a specific flag or type.
        sender: 'Pikita',
        time: new Date().toLocaleTimeString(),
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
    } else {
        console.error('WebSocket not connected');
        connectWebSocket();
    }
    viewGame();
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
