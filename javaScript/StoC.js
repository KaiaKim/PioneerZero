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
    // Generate or retrieve guest_id from localStorage
    let guest_id = localStorage.getItem('guest_id');
    if (!guest_id) {
        guest_id = crypto.randomUUID();
        localStorage.setItem('guest_id', guest_id);
    }

    ws.onopen = function() {
        console.log('WebSocket connected');
        fetch('http://127.0.0.1:7242/ingest/e1ba22a5-2e9e-4bc4-a632-a912cf61dec8',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'StoC.js:37',message:'WebSocket onopen',data:{guest_id:guest_id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
        // #endregion
        // Send guest_id to server
        ws.send(JSON.stringify({
            action: 'authenticate',
            guest_id: guest_id
        }));
// #endregion
        loadGame();
        
    };
    
    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data); //str -> Javascript object

        if (msg.type === "guest_assigned") {
            // Store guest_number in localStorage for display
            localStorage.setItem('guest_number', msg.guest_number);
            console.log(`You are Guest ${msg.guest_number}`);
        }
        else if (msg.type === "vomit_data") {
            console.log('Game data received');
            // Store game_id when game data is received (either from start_game or load_game)
            if (msg.game_id) {
                currentSessionId = msg.game_id;
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
        fetch('http://127.0.0.1:7242/ingest/e1ba22a5-2e9e-4bc4-a632-a912cf61dec8',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'StoC.js:86',message:'WebSocket onclose',data:{code:event.code,reason:event.reason,wasClean:event.wasClean},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'5'})}).catch(()=>{});
        // #endregion
    };
}