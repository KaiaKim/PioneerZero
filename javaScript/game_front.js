document.addEventListener('DOMContentLoaded', function() {
    // Extract game_id from URL
    const urlParams = new URLSearchParams(window.location.search);
    const gameIdFromUrl = urlParams.get('game_id');
    if (gameIdFromUrl) {
        setGameId(gameIdFromUrl);
    }
    
    // Set up chat input event listener
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
    
    // Connect to game WebSocket
    connectGameWebSocket();
});

