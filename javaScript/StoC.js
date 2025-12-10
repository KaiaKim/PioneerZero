// WebSocket connection
//(mostly) receive message from websocket server

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
        loadGame();
    };
    
    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data); //str -> Javascript object

        if (msg.type === "vomit_data") {
            console.log('Game data received');
            // Store session_id when game data is received (either from start_game or load_game)
            if (msg.session_id) {
                currentSessionId = msg.session_id;
            }
            viewMain();
            document.getElementById('vomit-box').value = JSON.stringify(msg, null, 2);
            loadTokens(msg.characters);
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
        else if (msg.type === "no_session") {
            console.log('No active session found');
            viewSelection();
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
    };
}